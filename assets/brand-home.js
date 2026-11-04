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

  // CMS content is pre-rendered by the publishing workflow, including hidden
  // records and bilingual metadata. Dialog delegation also covers new records.
})();
