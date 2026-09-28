async function loadArticles() {
  const status = document.getElementById('status');
  const list = document.getElementById('article-list');

  try {
    const res = await fetch('/api/articles');
    if (!res.ok) throw new Error(`Request failed: ${res.status}`);
    const articles = await res.json();

    if (articles.length === 0) {
      status.textContent = 'No articles yet.';
      return;
    }
    status.textContent = '';

    for (const article of articles) {
      const item = document.createElement('li');

      const link = document.createElement('a');
      link.href = `/article.html?id=${encodeURIComponent(article.id)}`;
      link.textContent = article.title;

      const meta = document.createElement('p');
      meta.className = 'meta';
      const date = new Date(article.updatedAt).toLocaleDateString(undefined, { timeZone: 'UTC' });
      const tags = article.tags.length ? ` · ${article.tags.join(', ')}` : '';
      meta.textContent = `${article.author} · ${date}${tags}`;

      item.append(link, meta);
      list.append(item);
    }
  } catch (err) {
    status.textContent = 'Could not load articles.';
    console.error(err);
  }
}

loadArticles();