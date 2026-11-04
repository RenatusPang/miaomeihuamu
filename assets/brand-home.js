/* Progressive enhancement: content and appointment links work without JavaScript. */
(() => {
  const menu = document.querySelector('.menu-button');
  const nav = document.querySelector('#primary-nav');
  const closeMenu = () => { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); menu.textContent = '菜单'; };
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    nav.classList.toggle('is-open', open); menu.setAttribute('aria-expanded', String(open)); menu.textContent = open ? '关闭' : '菜单';
  });
  nav.addEventListener('click', e => { if (e.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
  window.matchMedia('(min-width: 761px)').addEventListener('change', e => { if(e.matches) closeMenu(); });

  const filters = document.querySelectorAll('[data-filter]');
  const grid = document.querySelector('.work-grid');
  filters.forEach(button => button.addEventListener('click', () => {
    const selected = button.dataset.filter;
    filters.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    grid.classList.toggle('is-filtered', selected !== 'all');
    let count = 0;
    grid.querySelectorAll('.work').forEach(item => { item.hidden = selected !== 'all' && item.dataset.category !== selected; if(!item.hidden) count++; });
    document.querySelector('#filter-status').textContent = `已显示${count}组作品`;
  }));
  document.querySelector('.filters').hidden = false;

  const booking = document.querySelector('#booking-dialog');
  const lightbox = document.querySelector('#image-dialog');
  let lastTrigger;
  const openDialog = (dialog, trigger) => { lastTrigger = trigger; dialog.showModal(); };
  document.querySelectorAll('[data-book]').forEach(link => link.addEventListener('click', e => {
    if(typeof booking.showModal !== 'function') return;
    e.preventDefault(); closeMenu(); openDialog(booking, link);
  }));
  document.querySelectorAll('[data-image]').forEach(link => link.addEventListener('click', e => {
    if(typeof lightbox.showModal !== 'function') return;
    e.preventDefault();
    const source = link.querySelector('img');
    document.querySelector('#enlarged-image').src = link.href;
    document.querySelector('#enlarged-image').alt = source.alt;
    document.querySelector('#image-caption').textContent = source.alt;
    openDialog(lightbox, link);
  }));
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.querySelector('[data-close]').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', e => { if(e.target === dialog) { const r = dialog.getBoundingClientRect(); if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom) dialog.close(); } });
    dialog.addEventListener('close', () => { if(lastTrigger) lastTrigger.focus(); });
  });

  // Reuse the existing contact flow, including its manual-copy fallback.
  const copy = document.querySelector('#copy-wechat');
  const status = document.querySelector('#copy-wechat-status');
  function fallbackCopy(value) {
    const field = document.createElement('textarea'); field.value = value;
    field.style.position = 'fixed'; field.style.opacity = '0';
    document.body.appendChild(field); field.select();
    const result = document.execCommand('copy'); field.remove(); return result;
  }
  copy.addEventListener('click', async () => {
    const value = document.querySelector('#wechat-id').textContent.trim();
    let copied = false;
    try { if(navigator.clipboard?.writeText) { await navigator.clipboard.writeText(value); copied = true; } else copied = fallbackCopy(value); }
    catch { try { copied = fallbackCopy(value); } catch { /* Manual copy remains available. */ } }
    status.textContent = copied ? '已复制微信号，打开微信搜索添加。' : '复制未成功，请长按微信号手动复制。';
  });

  // Preserve the existing Pages CMS hero setting; accept only local image files.
  const assetURL = value => {
    if(typeof value !== 'string') return null;
    const url = new URL(value, location.href);
    return url.origin === location.origin && url.pathname.startsWith('/assets/') && /\.(webp|png|jpe?g)$/i.test(url.pathname) ? url.href : null;
  };
  (async () => {
    try {
      const response = await fetch('content/home.json'); if(!response.ok) return;
      const settings = await response.json(); const src = assetURL(settings.hero_image);
      if(src && src !== document.querySelector('#hero-image').src) { const test = new Image(); test.src = src; await test.decode(); document.querySelector('#hero-image').src = src; }
      if(typeof settings.hero_alt === 'string') document.querySelector('#hero-image').alt = settings.hero_alt;
      if(typeof settings.hero_badge === 'string') document.querySelector('#hero-badge').textContent = settings.hero_badge;
    } catch { /* Keep the pre-rendered image when configuration is unavailable. */ }
  })();
})();
