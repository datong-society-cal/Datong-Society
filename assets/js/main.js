/* Datong Society: dependency-free section navigation. */
(() => {
  const body = document.body;
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
    if (article.id === 'home') return;
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'close';
    close.setAttribute('aria-label', 'Close section and return home');
    close.textContent = 'Close';
    close.addEventListener('click', () => { location.hash = ''; });
    article.append(close);
  });
  main.hidden = true;

  function route({ initial = false } = {}) {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { id = ''; }
    id = ({ intro: 'about', work: 'workshops' })[id] || id;
    const current = sections.get(id);
    const wasOpen = body.classList.contains('is-article-visible');

    articles.forEach(article => {
      article.hidden = article !== current;
      article.classList.toggle('active', article === current);
    });
    main.hidden = !current;
    header.hidden = Boolean(current);
    sectionNav.hidden = !current;
    footer.hidden = Boolean(current) && id !== 'home';
    document.querySelector('.skip-link').href = current ? '#section-navigation' : '#site-navigation';
    body.classList.toggle('is-article-visible', Boolean(current));
    body.classList.toggle('is-home-visible', id === 'home');
    links.forEach(link => {
      if (link.hash === `#${id}` && current) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });

    if (current) {
      if (!wasOpen) previousFocus = document.activeElement;
      window.scrollTo(0, 0);
      if (!initial) {
        const focusTarget = current.querySelector('h1, h2');
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
