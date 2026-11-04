/* Progressive enhancement: content and appointment links work without JavaScript. */
(() => {
  const english = document.documentElement.lang === 'en';
  const words = (zh, en) => english ? en : zh;
  const menu = document.querySelector('.menu-button');
  const nav = document.querySelector('#primary-nav');
  const closeMenu = () => { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); menu.textContent = words('菜单', 'Menu'); };
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    nav.classList.toggle('is-open', open); menu.setAttribute('aria-expanded', String(open)); menu.textContent = open ? words('关闭', 'Close') : words('菜单', 'Menu');
  });
  nav.addEventListener('click', e => { if (e.target.closest('a')) closeMenu(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeMenu(); });
  window.matchMedia('(min-width: 961px)').addEventListener('change', e => { if(e.matches) closeMenu(); });
  const language = document.querySelector('.language-switch');
  const syncLanguageAnchor = () => {
    if (language) language.hash = location.hash;
  };
  syncLanguageAnchor();
  window.addEventListener('hashchange', syncLanguageAnchor);
  const revealHashTarget = () => {
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
    catch { return; }
    const detail = target?.closest('details');
    if (detail) {
      detail.open = true;
      requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
    }
  };
  revealHashTarget();
  window.addEventListener('hashchange', revealHashTarget);

  const booking = document.querySelector('#booking-dialog');
  const lightbox = document.querySelector('#image-dialog');
  let lastTrigger;
  const openDialog = (dialog, trigger) => { lastTrigger = trigger; dialog.showModal(); };
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

  // Preserve the existing Pages CMS hero setting; accept only local image files.
  const assetURL = value => {
    if(typeof value !== 'string') return null;
    const url = new URL(value, location.href);
    return url.origin === location.origin && url.pathname.startsWith('/assets/') && /\.(webp|png|jpe?g)$/i.test(url.pathname) ? url.href : null;
  };
  (async () => {
    try {
      const hero = document.querySelector('#hero-image');
      if (!hero) return;
      const response = await fetch('/content/home.json'); if(!response.ok) return;
      const settings = await response.json(); const src = assetURL(settings.hero_image);
      if(src && src !== document.querySelector('#hero-image').src) { const test = new Image(); test.src = src; await test.decode(); document.querySelector('#hero-image').src = src; }
      const alt = english ? settings.hero_alt_en : settings.hero_alt;
      const badge = english ? settings.hero_badge_en : settings.hero_badge;
      if(typeof alt === 'string') hero.alt = alt;
      if(typeof badge === 'string') document.querySelector('#hero-badge').textContent = badge;
    } catch { /* Keep the pre-rendered image when configuration is unavailable. */ }
  })();

  // Keep the existing Pages CMS galleries live; HTML remains available without JS.
  const categories = {
    'women-brow': 'Women’s brows', 'men-brow': 'Men’s brows',
    'lip-extension': 'Lip-contour refinement', 'hairline': 'Hairline pigmentation',
    'philtrum': 'Philtrum shading', 'eyeliner': 'Lash-line enhancement',
    'dark-lip-correction': 'Dark-lip colour correction'
  };
  document.querySelectorAll('[data-gallery]').forEach(group => {
    const category = group.dataset.gallery;
    if (!Object.hasOwn(categories, category)) return;
    (async () => {
      try {
        const response = await fetch(`/content/works/${category}.json`);
        if (!response.ok) return;
        const records = await response.json();
        if (!Array.isArray(records) || records.some(record => !record || typeof record !== 'object' || typeof record.published !== 'boolean')) return;
        const fragment = document.createDocumentFragment();
        let count = 0;
        for (const record of records) {
          if (record.published !== true) continue;
          const src = assetURL(record.image);
          let videoURL = null;
          if (typeof record.video === 'string' && record.video) {
            const candidate = new URL(record.video, location.href);
            if (candidate.origin === location.origin && candidate.pathname.startsWith('/assets/') && /\.(mp4|webm)$/i.test(candidate.pathname)) videoURL = candidate.href;
          }
          if (!src && !videoURL) continue;
          count++;
          const title = english ? record.title_en || `${categories[category]} · Work record ${count}` : record.title || '作品记录';
          const alt = english ? record.alt_en || title : record.alt || title;
          const description = english ? record.description_en : record.description;
          const figure = document.createElement('figure');
          if (src) {
            const link = document.createElement('a'); link.href = src; link.dataset.image = '';
            const img = document.createElement('img'); img.src = src; img.alt = alt; img.loading = 'lazy';
            link.append(img); figure.append(link);
          } else {
            const video = document.createElement('video'); video.src = videoURL;
            video.controls = true; video.playsInline = true; video.preload = 'none';
            video.setAttribute('aria-label', alt); figure.append(video);
          }
          const caption = document.createElement('figcaption');
          const heading = document.createElement('h3'); heading.textContent = title; caption.append(heading);
          if (typeof description === 'string' && description.trim()) {
            const p = document.createElement('p'); p.textContent = description; caption.append(p);
          }
          figure.append(caption); fragment.append(figure);
        }
        // A valid empty list must also remove records that are no longer public.
        group.querySelector('.archive-grid').replaceChildren(fragment);
        group.querySelector('.gallery-count').textContent = `${count} ${words('组记录', 'records')}`;
        group.hidden = count === 0;
      } catch { /* The existing static work records remain readable. */ }
    })();
  });
})();
