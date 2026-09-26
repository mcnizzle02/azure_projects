import base64
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import azure.functions as func
from azure.cosmos import CosmosClient, exceptions

READ_ROLES = {"reader", "contributor", "admin"}
WRITE_ROLES = {"contributor", "admin"}

MAX_TITLE = 200
MAX_BODY = 50_000
MAX_TAGS = 10
MAX_TAG_LEN = 30

_client = None


def get_container():
    global _client
    if _client is None:
        _client = CosmosClient(
            os.environ["COSMOS_ENDPOINT"],
            credential=os.environ["COSMOS_KEY"],
        )
    database = _client.get_database_client(os.environ["COSMOS_DATABASE"])
    return database.get_container_client(os.environ["COSMOS_CONTAINER"])


def get_principal(req: func.HttpRequest) -> dict:
    """Decode the identity Static Web Apps attaches to every request."""
    header = req.headers.get("x-ms-client-principal")
    if not header:
        return {}
    try:
        return json.loads(base64.b64decode(header))
    except ValueError:
        return {}


def json_response(body, status=200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body), status_code=status, mimetype="application/json"
    )


def clean(item: dict) -> dict:
    return {k: v for k, v in item.items() if not k.startswith("_")}


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_article(data):
    """Return (article, None) if valid, or (None, error message)."""
    if not isinstance(data, dict):
        return None, "request body must be a JSON object"

    title = data.get("title")
    body = data.get("body")
    tags = data.get("tags", [])

    if not isinstance(title, str) or not title.strip() or len(title) > MAX_TITLE:
        return None, f"title is required and must be at most {MAX_TITLE} characters"
    if not isinstance(body, str) or not body.strip() or len(body) > MAX_BODY:
        return None, f"body is required and must be at most {MAX_BODY} characters"
    if (
        not isinstance(tags, list)
        or len(tags) > MAX_TAGS
        or not all(
            isinstance(t, str) and 0 < len(t.strip()) <= MAX_TAG_LEN for t in tags
        )
    ):
        return None, f"tags must be a list of up to {MAX_TAGS} strings, each at most {MAX_TAG_LEN} characters"

    # Build a NEW dict with only the allowed fields. Anything else the
    # client sent (id, author, createdAt, admin flags...) is dropped.
    return {
        "title": title.strip(),
        "body": body,
        "tags": [t.strip().lower() for t in tags],
    }, None


def get_articles(req, container):
    article_id = req.route_params.get("id")
    if article_id:
        item = container.read_item(item=article_id, partition_key=article_id)
        return json_response(clean(item))

    items = container.query_items(
        query=(
            "SELECT c.id, c.title, c.tags, c.author, c.updatedAt "
            "FROM c ORDER BY c.updatedAt DESC"
        ),
        enable_cross_partition_query=True,
    )
    return json_response(list(items))


def create_article(req, container, principal, roles):
    if req.route_params.get("id"):
        return json_response({"error": "method not allowed"}, 405)
    if not roles & WRITE_ROLES:
        return json_response({"error": "forbidden"}, 403)

    try:
        data = req.get_json()
    except ValueError:
        return json_response({"error": "invalid JSON"}, 400)

    article, error = validate_article(data)
    if error:
        return json_response({"error": error}, 400)

    now = utc_now()
    article.update(
        {
            "id": str(uuid.uuid4()),
            "author": principal.get("userDetails", "unknown"),
            "createdAt": now,
            "updatedAt": now,
        }
    )
    created = container.create_item(body=article)
    return json_response(clean(created), 201)


def main(req: func.HttpRequest) -> func.HttpResponse:
    principal = get_principal(req)
    roles = set(principal.get("userRoles", []))

    if not roles & READ_ROLES:
        return json_response({"error": "forbidden"}, 403)

    try:
        container = get_container()
        if req.method == "POST":
            return create_article(req, container, principal, roles)
        return get_articles(req, container)

    except exceptions.CosmosResourceNotFoundError:
        return json_response({"error": "not found"}, 404)
    except exceptions.CosmosHttpResponseError:
        logging.exception("Cosmos DB request failed")
        return json_response({"error": "server error"}, 500)