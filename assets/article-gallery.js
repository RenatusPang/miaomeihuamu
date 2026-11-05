/* Extend the existing image dialog only on the illustrated article. */
(() => {
  const gallery = document.querySelector('[data-article-gallery]');
  const dialog = document.querySelector('#image-dialog');
  const controls = document.querySelector('.article-gallery-controls');
  if (!gallery || !dialog || !controls) return;
  const links = [...gallery.querySelectorAll('a[data-image]')];
  const picture = dialog.querySelector('#enlarged-image');
  const caption = dialog.querySelector('#image-caption');
  const position = controls.querySelector('[data-gallery-position]');
  const viewport = dialog.querySelector('.article-image-viewport');
  const zoom = controls.querySelector('[data-gallery-zoom]');
  let current = -1;
  let touchStart = null;
  let zoomed = false;

  function setZoom(value) {
    zoomed = value;
    touchStart = null;
    viewport.classList.toggle('is-zoomed', value);
    viewport.style.setProperty('--article-image-width', `${picture.naturalWidth || 1180}px`);
    viewport.scrollTo(0, 0);
    zoom.setAttribute('aria-pressed', String(value));
    zoom.textContent = value ? zoom.dataset.fitLabel : zoom.dataset.zoomLabel;
  }
  zoom.addEventListener('click', () => setZoom(!zoomed));
  picture.addEventListener('load', () => {
    viewport.style.setProperty('--article-image-width', `${picture.naturalWidth}px`);
  });

  function select(index) {
    if (!links.length) return;
    setZoom(false);
    current = (index + links.length) % links.length;
    const link = links[current];
    picture.src = link.href;
    picture.alt = link.querySelector('img').alt;
    caption.textContent = picture.alt;
    position.textContent = `${current + 1} / ${links.length}`;
  }

  document.addEventListener('click', event => {
    const link = event.target.closest('[data-article-gallery] a[data-image]');
    if (!link || !dialog.open) return;
    select(links.indexOf(link));
  });
  controls.querySelector('[data-gallery-previous]').addEventListener('click', () => select(current - 1));
  controls.querySelector('[data-gallery-next]').addEventListener('click', () => select(current + 1));
  dialog.addEventListener('keydown', event => {
    if (!dialog.open || current < 0 || event.altKey || event.ctrlKey || event.metaKey) return;
    if (zoomed && viewport.contains(event.target)) return;
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      select(current + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  picture.addEventListener('touchstart', event => {
    touchStart = !zoomed && event.touches.length === 1
      ? { x: event.touches[0].clientX, y: event.touches[0].clientY } : null;
  }, { passive: true });
  picture.addEventListener('touchmove', event => {
    if (event.touches.length !== 1) touchStart = null;
  }, { passive: true });
  picture.addEventListener('touchend', event => {
    if (!touchStart || event.changedTouches.length !== 1 || event.touches.length) return;
    const dx = event.changedTouches[0].clientX - touchStart.x;
    const dy = event.changedTouches[0].clientY - touchStart.y;
    touchStart = null;
    if (Math.abs(dx) >= 50 && Math.abs(dx) > Math.abs(dy) * 1.5) select(current + (dx < 0 ? 1 : -1));
  }, { passive: true });
  picture.addEventListener('touchcancel', () => { touchStart = null; }, { passive: true });
  dialog.addEventListener('close', () => { current = -1; setZoom(false); });
})();
