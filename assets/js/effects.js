/* Progressive enhancements. The content and links remain available without JavaScript. */
(() => {
  const filter = document.querySelector('#events-filter');
  const cards = [...document.querySelectorAll('.event-card')];
  filter?.addEventListener('click', event => {
    const button = event.target.closest('button[data-filter]');
    if (!button || !filter.contains(button)) return;
    filter.querySelectorAll('button').forEach(item => {
      const selected = item === button;
      item.classList.toggle('is-active', selected);
      item.setAttribute('aria-pressed', String(selected));
    });
    const category = button.dataset.filter;
    cards.forEach(card => {
      card.hidden = category !== 'all' && card.dataset.cat !== category;
    });
  });
  filter?.querySelectorAll('button').forEach(button => {
    button.setAttribute('aria-pressed', String(button.classList.contains('is-active')));
  });

  const overlay = document.querySelector('#lb-overlay');
  const overlayImage = document.querySelector('#lb-img');
  const overlayCaption = document.querySelector('#lb-cap');
  let imageTrigger = null;
  if (overlay) {
    overlay.setAttribute('role', 'dialog');
    overlay.setAttribute('aria-modal', 'true');
    overlay.setAttribute('aria-label', 'Event image');
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'lb-close';
    close.setAttribute('aria-label', 'Close image');
    close.textContent = '×';
    overlay.append(close);

    function closeImage() {
      overlay.classList.remove('is-open');
      overlayImage.removeAttribute('src');
      imageTrigger?.focus({ preventScroll: true });
      imageTrigger = null;
    }
    close.addEventListener('click', closeImage);
    overlay.addEventListener('click', event => {
      if (event.target === overlay) closeImage();
    });
    document.addEventListener('keydown', event => {
      if (!overlay.classList.contains('is-open')) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopImmediatePropagation();
        closeImage();
      } else if (event.key === 'Tab') {
        event.preventDefault();
        close.focus();
      }
    }, true);

    document.querySelectorAll('.event-cover img, .event-gallery a').forEach(trigger => {
      if (trigger.matches('img')) {
        trigger.tabIndex = 0;
        trigger.setAttribute('role', 'button');
        trigger.setAttribute('aria-label', `Enlarge ${trigger.alt || 'event image'}`);
        trigger.addEventListener('keydown', event => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            trigger.click();
          }
        });
      }
      trigger.addEventListener('click', event => {
        event.preventDefault();
        imageTrigger = trigger;
        const card = trigger.closest('.event-card');
        const heading = card?.querySelector('h3');
        const caption = trigger.dataset.cap || heading?.textContent.trim() || '';
        overlayImage.src = trigger.matches('a') ? trigger.href : trigger.src;
        overlayImage.alt = caption;
        overlayCaption.textContent = caption;
        overlay.classList.add('is-open');
        close.focus({ preventScroll: true });
      });
    });
  }

  const background = document.querySelector('#bg');
  const logo = document.querySelector('.article-logo');
  const ticks = logo?.querySelector('.ring-ticks');
  const progressRing = logo?.querySelector('.ring-progress');
  const progressHead = logo?.querySelector('.ring-head');
  const radius = 64;
  const circumference = 2 * Math.PI * radius;
  let scheduled = false;

  if (ticks && progressRing && progressHead) {
    const svgNS = 'http://www.w3.org/2000/svg';
    for (let index = 0; index < 24; index++) {
      const angle = (index * 15 - 90) * Math.PI / 180;
      const major = index % 6 === 0;
      const start = major ? 66.5 : 67.5;
      const end = major ? 72 : 71;
      const line = document.createElementNS(svgNS, 'line');
      line.setAttribute('x1', (74 + start * Math.cos(angle)).toFixed(2));
      line.setAttribute('y1', (74 + start * Math.sin(angle)).toFixed(2));
      line.setAttribute('x2', (74 + end * Math.cos(angle)).toFixed(2));
      line.setAttribute('y2', (74 + end * Math.sin(angle)).toFixed(2));
      line.setAttribute('class', major ? 'tick tick-major' : 'tick');
      ticks.append(line);
    }
    progressRing.style.strokeDasharray = String(circumference);
  }

  function renderScroll() {
    scheduled = false;
    const max = Math.max(0, document.documentElement.scrollHeight - innerHeight);
    const scroll = Math.max(0, scrollY);
    const progress = max > 4 ? Math.min(1, scroll / max) : 0;
    const articleOpen = document.body.classList.contains('is-article-visible');
    background?.style.setProperty('--bg-shift', articleOpen ? progress.toFixed(4) : '0');
    if (!articleOpen || !progressRing) return;
    progressRing.style.strokeDashoffset = String(circumference * (1 - progress));
    const angle = (progress * 360 - 90) * Math.PI / 180;
    progressHead.setAttribute('cx', String(74 + radius * Math.cos(angle)));
    progressHead.setAttribute('cy', String(74 + radius * Math.sin(angle)));
    progressHead.style.opacity = progress > .002 ? '1' : '0';
  }
  function scheduleScroll() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(renderScroll);
  }
  addEventListener('scroll', scheduleScroll, { passive: true });
  addEventListener('resize', scheduleScroll);
  addEventListener('datong:route', scheduleScroll);
  addEventListener('load', scheduleScroll);
  scheduleScroll();
})();
