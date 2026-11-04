'use strict';
const fileInput = document.querySelector('#file');
const quality = document.querySelector('#quality');
const convert = document.querySelector('#convert');
const result = document.querySelector('#result');
const download = document.querySelector('#download');
let originalURL, outputURL, file, sourceImage;
const size = bytes => `${(bytes / 1024 / 1024).toFixed(2)} MiB`;
quality.addEventListener('input', () => { document.querySelector('#quality-value').textContent = quality.value; });
fileInput.addEventListener('change', async () => {
  convert.disabled = true; download.hidden = true; file = fileInput.files[0];
  if (originalURL) URL.revokeObjectURL(originalURL);
  if (!file) { result.textContent = '尚未选择图片。'; return; }
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) { result.textContent = '请选择 JPG、PNG 或 WebP。'; return; }
  if (file.size > 40 * 1024 * 1024) { result.textContent = '原图超过 40 MiB，请先从相册导出较小版本。'; return; }
  try {
    originalURL = URL.createObjectURL(file);
    sourceImage = new Image(); sourceImage.src = originalURL; await sourceImage.decode();
    document.querySelector('#original').src = originalURL;
    document.querySelector('#original-link').href = originalURL;
    result.textContent = `原图 ${sourceImage.naturalWidth} × ${sourceImage.naturalHeight}，${size(file.size)}。`;
    convert.disabled = false;
  } catch { result.textContent = '无法读取这张图片，请换 JPG、PNG 或 WebP 文件。'; }
});
convert.addEventListener('click', async () => {
  if (!sourceImage) return;
  convert.disabled = true; download.hidden = true;
  try {
    const edge = Number(document.querySelector('#edge').value);
    const scale = edge ? Math.min(1, edge / Math.max(sourceImage.naturalWidth, sourceImage.naturalHeight)) : 1;
    const canvas = document.createElement('canvas');
    canvas.width = Math.round(sourceImage.naturalWidth * scale); canvas.height = Math.round(sourceImage.naturalHeight * scale);
    const context = canvas.getContext('2d'); context.imageSmoothingQuality = 'high';
    context.drawImage(sourceImage, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/webp', Number(quality.value) / 100));
    if (!blob) throw Error('图片转换失败');
    if (outputURL) URL.revokeObjectURL(outputURL);
    outputURL = URL.createObjectURL(blob);
    document.querySelector('#output').src = outputURL; document.querySelector('#output-link').href = outputURL;
    download.href = outputURL; download.download = file.name.replace(/\.[^.]+$/, '') + (blob.type === 'image/webp' ? '-web.webp' : '-web.png'); download.hidden = false;
    result.textContent = `${canvas.width} × ${canvas.height}，${size(blob.size)}，原图 ${size(file.size)}。${blob.size >= file.size ? '文件未变小，可直接使用原图。' : '下载前请放大核对毛流细节。'}`;
  } catch (error) { result.textContent = error.message; }
  finally { convert.disabled = false; }
});
