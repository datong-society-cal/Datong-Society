/* Explicit language selection; preserve the current section. */
(() => {
  const link = document.querySelector('.language-switch a');
  if (!link) return;
  const destination = link.getAttribute('href').split('#')[0];
  const update = () => { link.href = destination + location.hash; };
  update();
  addEventListener('hashchange', update);
})();
