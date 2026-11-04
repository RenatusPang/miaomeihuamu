/* Progressive enhancement: content and appointment links work without JavaScript. */
(() => {
  const english = document.documentElement.lang === 'en';
  const words = (zh, en) => english ? en : zh;
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const compactMotion = window.matchMedia('(max-width: 760px)');
  const activeMotion = new Set();
  const ease = 'cubic-bezier(.22,.68,.16,1)';
  const canAnimate = () => !reducedMotion.matches && typeof Element.prototype.animate === 'function';
  // No persistent hidden class or inline opacity. If enhancement fails, the
  // underlying static page remains visible; each finite animation releases it.
  function animate(element, frames, options = {}) {
    if (!element || !canAnimate()) return null;
    try {
      const animation = element.animate(frames, { duration: compactMotion.matches ? 380 : 640, easing: ease, fill: 'backwards', ...options });
      activeMotion.add(animation);
      animation.finished.then(() => activeMotion.delete(animation), () => activeMotion.delete(animation));
      return animation;
    } catch { return null; }
  }
  function settleMotion() {
    activeMotion.forEach(animation => animation.cancel());
    activeMotion.clear();
  }
  reducedMotion.addEventListener('change', event => { if (event.matches) settleMotion(); });
  window.addEventListener('pageshow', event => { if (event.persisted) settleMotion(); });
  document.addEventListener('focusin', event => {
    activeMotion.forEach(animation => {
      if (animation.effect?.target?.contains(event.target)) animation.cancel();
    });
  });
  const menu = document.querySelector('.menu-button');
  const nav = document.querySelector('#primary-nav');
  let menuAnimation, menuTimer;
  const setMenu = open => {
    clearTimeout(menuTimer);
    menuAnimation?.cancel();
    menu.setAttribute('aria-expanded', String(open));
    menu.textContent = open ? words('关闭', 'Close') : words('菜单', 'Menu');
    if (open) {
      nav.classList.add('is-open');
      nav.inert = false;
      menuAnimation = animate(nav, [{ opacity: .3, transform: 'translateY(-4px)' }, { opacity: 1, transform: 'none' }], { duration: 220 });
    } else {
      const finish = () => { nav.classList.remove('is-open'); nav.inert = false; };
      if (!nav.classList.contains('is-open') || !canAnimate() || window.innerWidth > 960) return finish();
      nav.inert = true;
      menuAnimation = animate(nav, [{ opacity: 1 }, { opacity: 0 }], { duration: 140 });
      // A timer also completes the interaction if the animation is cancelled.
      menuTimer = setTimeout(finish, 140);
    }
  };
  const closeMenu = () => setMenu(false);
  menu.addEventListener('click', () => {
    setMenu(menu.getAttribute('aria-expanded') !== 'true');
  });
  nav.addEventListener('click', e => { if (e.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') { closeMenu(); menu.focus(); }
  });
  window.matchMedia('(min-width: 961px)').addEventListener('change', e => { if(e.matches) closeMenu(); });
  document.querySelector('.site-header').classList.add('menu-ready');
  const language = document.querySelector('.language-switch');
  const syncLanguageAnchor = () => {
    if (language) language.hash = location.hash;
  };
  syncLanguageAnchor();
  window.addEventListener('hashchange', syncLanguageAnchor);
  const detailControls = new WeakMap();
  const revealHashTarget = () => {
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
    catch { return; }
    const detail = target?.closest('details');
    if (detail) {
      if (detailControls.has(detail)) detailControls.get(detail).open();
      else detail.open = true;
      requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
    }
  };
  revealHashTarget();
  window.addEventListener('hashchange', revealHashTarget);

  const booking = document.querySelector('#booking-dialog');
  const lightbox = document.querySelector('#image-dialog');
  let lastTrigger;
  const dialogMotion = new WeakMap();
  const openDialog = (dialog, trigger) => {
    if (dialog.open) return;
    lastTrigger = trigger;
    dialog.showModal();
    dialogMotion.set(dialog, animate(dialog, [
      { opacity: .1, transform: `translateY(${compactMotion.matches ? 4 : 8}px) scale(.99)` },
      { opacity: 1, transform: 'none' }
    ], { duration: compactMotion.matches ? 200 : 300 }));
  };
  const closeDialog = dialog => {
    if (!dialog.open || dialog.hasAttribute('data-closing')) return;
    dialogMotion.get(dialog)?.cancel();
    if (!canAnimate()) { dialog.close(); return; }
    dialog.setAttribute('data-closing', '');
    let timer;
    const finish = () => {
      clearTimeout(timer);
      if (!dialog.hasAttribute('data-closing')) return;
      dialog.removeAttribute('data-closing');
      dialog.close();
    };
    timer = setTimeout(finish, 180);
    const animation = animate(dialog, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(3px)' }], { duration: 160 });
    animation?.finished.then(finish, finish);
  };
  document.querySelectorAll('[data-book]').forEach(link => link.addEventListener('click', e => {
    if(typeof booking.showModal !== 'function') return;
    e.preventDefault(); closeMenu(); openDialog(booking, link);
  }));
  document.addEventListener('click', e => {
    const link = e.target.closest('a[data-image]');
    if (!link) return;
    if(typeof lightbox.showModal !== 'function') return;
    e.preventDefault();
    const source = link.querySelector('img');
    document.querySelector('#enlarged-image').src = link.href;
    document.querySelector('#enlarged-image').alt = source.alt;
    document.querySelector('#image-caption').textContent = source.alt;
    openDialog(lightbox, link);
  });
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.querySelector('[data-close]').addEventListener('click', () => closeDialog(dialog));
    dialog.addEventListener('cancel', e => { e.preventDefault(); closeDialog(dialog); });
    dialog.addEventListener('click', e => { if(e.target === dialog) { const r = dialog.getBoundingClientRect(); if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom) closeDialog(dialog); } });
    dialog.addEventListener('close', () => {
      if (!lastTrigger?.isConnected) return;
      const unavailable = lastTrigger.closest('details:not([open])') || lastTrigger.closest('[inert]')?.closest('details');
      const target = unavailable?.querySelector('summary') || lastTrigger;
      if (target.getClientRects().length) target.focus({ preventScroll: true });
    });
  });

  // Keep the native details structure, URLs, keyboard controls and no-JS path.
  // Long galleries fade instead of pushing an entire page through a height tween.
  document.querySelectorAll('.archive-group, .service, .faq').forEach(detail => {
    const summary = detail.querySelector(':scope > summary');
    const content = summary?.nextElementSibling;
    if (!content) return;
    let opening = detail.open, transition, contentMotion, timer;
    const reset = open => {
      clearTimeout(timer); timer = null;
      transition?.cancel(); contentMotion?.cancel();
      detail.style.removeProperty('height'); detail.style.removeProperty('overflow');
      content.inert = false;
      opening = open; detail.open = open;
    };
    detailControls.set(detail, { open: () => reset(true) });
    reducedMotion.addEventListener('change', event => { if (event.matches && timer) reset(opening); });
    summary.addEventListener('click', event => {
      if (!canAnimate()) {
        reset(detail.open);
        return;
      }
      event.preventDefault();
      clearTimeout(timer);
      const from = detail.getBoundingClientRect().height;
      transition?.cancel(); contentMotion?.cancel();
      opening = !opening;
      detail.style.removeProperty('height');
      detail.style.removeProperty('overflow');
      detail.open = true;
      if (!opening && content.contains(document.activeElement)) summary.focus({ preventScroll: true });
      content.inert = !opening;
      const expanded = detail.getBoundingClientRect().height;
      const collapsed = summary.getBoundingClientRect().height + 1;
      const duration = compactMotion.matches ? 200 : 280;
      const finish = () => {
        clearTimeout(timer); timer = null;
        detail.open = opening;
        content.inert = false;
        detail.style.removeProperty('height');
        detail.style.removeProperty('overflow');
      };
      // Install cleanup before starting an optional animation.
      timer = setTimeout(finish, duration);
      if (expanded - collapsed < 700) {
        detail.style.overflow = 'hidden';
        transition = animate(detail, [{ height: `${from}px` }, { height: `${opening ? expanded : collapsed}px` }], { duration });
      }
      const visible = { opacity: 1, transform: 'none' };
      const quiet = { opacity: 0, transform: `translateY(${compactMotion.matches ? 2 : 5}px)` };
      contentMotion = animate(content, opening ? [quiet, visible] : [visible, quiet], { duration });
    });
    detail.addEventListener('toggle', () => { if (!timer) opening = detail.open; });
  });

  // Reuse the existing contact flow, including its manual-copy fallback.
  const copy = document.querySelector('#copy-wechat');
  const status = document.querySelector('#copy-wechat-status');
  function fallbackCopy(value) {
    const field = document.createElement('textarea'); field.value = value;
    field.style.position = 'fixed'; field.style.opacity = '0';
    (document.querySelector('dialog[open]') || document.body).appendChild(field); field.select();
    const result = document.execCommand('copy'); field.remove(); return result;
  }
  copy.addEventListener('click', async () => {
    const value = document.querySelector('#wechat-id').textContent.trim();
    let copied = false;
    try { if(navigator.clipboard?.writeText) { await navigator.clipboard.writeText(value); copied = true; } else copied = fallbackCopy(value); }
    catch { try { copied = fallbackCopy(value); } catch { /* Manual copy remains available. */ } }
    status.textContent = copied ? words('已复制微信号，打开微信搜索添加。', 'WeChat ID copied. Search for it in WeChat.') : words('复制未成功，请长按微信号手动复制。', 'Copy did not succeed. Select and copy the ID manually.');
  });

  // CMS content is pre-rendered by the publishing workflow, including hidden
  // records and bilingual metadata. Dialog delegation also covers new records.

  // Observe only editorial landmarks, not every paragraph or archive record.
  // Elements are visible before observation, during failures, and after playback.
  if ('IntersectionObserver' in window && canAnimate()) {
    const observed = new WeakMap();
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        const kind = observed.get(entry.target);
        const distance = compactMotion.matches ? 5 : 12;
        let frames = [{ opacity: .25, transform: `translateY(${distance}px)` }, { opacity: 1, transform: 'none' }];
        if (kind === 'image') frames = [{ opacity: .55, clipPath: 'inset(0 0 5% 0)' }, { opacity: 1, clipPath: 'inset(0)' }];
        if (kind === 'quiet') frames = [{ opacity: .4 }, { opacity: 1 }];
        animate(entry.target, frames, { duration: compactMotion.matches ? 380 : (kind === 'image' ? 820 : kind === 'quiet' ? 520 : 640) });
      });
    }, { rootMargin: '0px 0px 24px 0px', threshold: 0 });
    const groups = [
      ['.section-heading, .approach-inner > div:first-child, .layer-story > div, .services-layout > div:first-child, .artist-copy, .visit h2', 'rise'],
      ['.case-item > a, .layer-story figure > a, .closeup-pair figure > a', 'image'],
      ['.approach-item, .case-item figcaption, .artist-image, .journal-editorial, .closeup-pair > div', 'quiet']
    ];
    groups.forEach(([selector, kind]) => document.querySelectorAll(selector).forEach(element => {
      observed.set(element, kind); observer.observe(element);
    }));
    reducedMotion.addEventListener('change', event => { if (event.matches) observer.disconnect(); });
  }
})();
