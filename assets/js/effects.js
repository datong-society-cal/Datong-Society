/* Progressive enhancements. The content and links remain available without JavaScript. */
(() => {
  const chinese = document.documentElement.lang.startsWith('zh');
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
    overlay.setAttribute('aria-label', chinese ? '活动图片' : 'Event image');
    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'lb-close';
    close.setAttribute('aria-label', chinese ? '关闭图片' : 'Close image');
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
        trigger.setAttribute('aria-label', chinese ? `放大：${trigger.alt || '活动图片'}` : `Enlarge ${trigger.alt || 'event image'}`);
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

})();
