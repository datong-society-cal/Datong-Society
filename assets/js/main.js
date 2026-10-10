/* Datong Society: dependency-free section navigation. */
(() => {
  const body = document.body;
  const chinese = document.documentElement.lang.startsWith('zh');
  const header = document.querySelector('#header');
  const footer = document.querySelector('#footer');
  const main = document.querySelector('#main');
  const articles = [...main.querySelectorAll(':scope > article')];
  const sections = new Map(articles.map(article => [article.id, article]));
  const sectionNav = header.querySelector('nav').cloneNode(true);
  sectionNav.id = 'section-navigation';
  sectionNav.className = 'section-navigation';
  sectionNav.setAttribute('aria-label', 'Section navigation');
  document.body.append(sectionNav);
  const links = [...document.querySelectorAll('nav a[href^="#"]')];
  let previousFocus = null;

  articles.forEach(article => {
    article.hidden = true;
    const affiliation = document.createElement('p');
    affiliation.className = 'article-affiliation';
    affiliation.innerHTML = 'A registered student organization at UC Berkeley · <a href="https://callink.berkeley.edu/organization/datongsocietyofchinastudies" target="_blank" rel="noopener noreferrer">CalLink listing</a><br>We are a student group acting independently of the University of California. We take full responsibility for our organization and this web site.';
    article.append(affiliation);
    if (chinese) affiliation.innerHTML = '加州大学伯克利分校注册学生组织 · <a href="https://callink.berkeley.edu/organization/datongsocietyofchinastudies" target="_blank" rel="noopener noreferrer">CalLink 登记</a><br>我们是独立于加州大学运营的学生组织，对本组织及本网站承担全部责任。';
    if (article.id === 'home') { affiliation.remove(); return; }
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'close';
    close.setAttribute('aria-label', chinese ? '关闭栏目并返回首页' : 'Close section and return home');
    close.textContent = chinese ? '关闭' : 'Close';
    close.addEventListener('click', () => { location.hash = ''; });
    article.append(close);
  });
  main.hidden = true;

  function route({ initial = false } = {}) {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { id = ''; }
    id = ({ intro: 'about', work: 'workshops' })[id] || id || 'home';
    if (!sections.has(id)) id = 'home';
    const current = sections.get(id);
    const isHome = id === 'home';
    const wasOpen = body.classList.contains('is-article-visible');

    articles.forEach(article => {
      article.hidden = article !== current;
      article.classList.toggle('active', article === current);
    });
    main.hidden = !current;
    header.hidden = !isHome;
    sectionNav.hidden = isHome;
    footer.hidden = !isHome;
    document.querySelector('.skip-link').href = isHome ? '#site-navigation' : '#section-navigation';
    body.classList.toggle('is-article-visible', !isHome);
    body.classList.toggle('is-home-visible', isHome);
    links.forEach(link => {
      if (link.hash === `#${id}` && current) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });

    if (current) {
      if (!wasOpen) previousFocus = document.activeElement;
      window.scrollTo(0, 0);
      if (!initial) {
        const focusTarget = isHome ? header.querySelector('h1') : current.querySelector('h1, h2');
        focusTarget?.setAttribute('tabindex', '-1');
        focusTarget?.focus({ preventScroll: true });
      }
    } else if (wasOpen) {
      window.scrollTo(0, 0);
      const target = previousFocus?.isConnected ? previousFocus : header.querySelector('nav a');
      target?.focus({ preventScroll: true });
    }
    window.dispatchEvent(new Event('datong:route'));
  }

  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    if (document.querySelector('#lb-overlay.is-open')) return;
    if (body.classList.contains('is-article-visible')) location.hash = '';
  });
  window.addEventListener('hashchange', () => route());
  if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
  route({ initial: true });
  requestAnimationFrame(() => body.classList.remove('is-preload'));
})();
