import base64
import json
import logging
import os

import azure.functions as func
from azure.cosmos import CosmosClient, exceptions

READ_ROLES = {"reader", "contributor", "admin"}

# Created once and reused while the Function stays warm,
# instead of opening a new connection on every request.
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


def get_roles(req: func.HttpRequest) -> set:
    """Read the signed-in user's roles from the header Static Web Apps adds."""
    header = req.headers.get("x-ms-client-principal")
    if not header:
        return set()
    try:
        principal = json.loads(base64.b64decode(header))
        return set(principal.get("userRoles", []))
    except ValueError:
        return set()


def json_response(body, status=200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(body), status_code=status, mimetype="application/json"
    )


def clean(item: dict) -> dict:
    """Remove Cosmos system fields (_rid, _self, _etag...) before returning."""
    return {k: v for k, v in item.items() if not k.startswith("_")}


def main(req: func.HttpRequest) -> func.HttpResponse:
    if not get_roles(req) & READ_ROLES:
        return json_response({"error": "forbidden"}, 403)

    article_id = req.route_params.get("id")

    try:
        container = get_container()
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

    except exceptions.CosmosResourceNotFoundError:
        return json_response({"error": "not found"}, 404)
    except exceptions.CosmosHttpResponseError:
        logging.exception("Cosmos DB request failed")
        return json_response({"error": "server error"}, 500)