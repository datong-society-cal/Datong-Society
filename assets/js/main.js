/* Preserve bookmarked legacy section URLs; pages work without JavaScript. */
(() => {
  const pages = { home: 'index', about: 'about', intro: 'about', work: 'workshops', workshops: 'workshops', events: 'events', resources: 'resources', contact: 'contact' };
  const chinese = document.documentElement.lang.startsWith('zh');
  const redirect = () => {
    const page = pages[location.hash.slice(1)];
    if (page && document.body.classList.contains('page-home')) {
      const filename = page === 'index' ? (chinese ? 'zh.html' : 'index.html') : page + (chinese ? '-zh' : '') + '.html';
      location.replace(filename);
    }
  };
  redirect();
  addEventListener('hashchange', redirect);
})();
