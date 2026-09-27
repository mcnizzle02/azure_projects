async function loadArticle() {
  const status = document.getElementById('status');
  const id = new URLSearchParams(window.location.search).get('id');

  if (!id) {
    status.textContent = 'No article specified.';
    return;
  }

  try {
    const res = await fetch(`/api/articles/${encodeURIComponent(id)}`);
    if (res.status === 404) {
      status.textContent = 'Article not found.';
      return;
    }
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const article = await res.json();

    document.title = `${article.title} · Cloud Knowledge Base`;
    document.getElementById('title').textContent = article.title;

    const date = new Date(article.updatedAt).toLocaleDateString();
    const tags = article.tags.length ? ` · ${article.tags.join(', ')}` : '';
    document.getElementById('meta').textContent =
      `${article.author} · Updated ${date}${tags}`;

    // The ONLY place HTML is inserted: Markdown is converted to HTML,
    // then sanitized so nothing in it can run code.
    const rawHtml = marked.parse(article.body);
    document.getElementById('body').innerHTML = DOMPurify.sanitize(rawHtml);

    status.hidden = true;
    document.getElementById('article').hidden = false;
  } catch (err) {
    status.textContent = 'Could not load this article.';
    console.error(err);
  }
}

loadArticle();