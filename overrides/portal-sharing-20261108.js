(() => {
  'use strict';
  const metaElement = document.getElementById('portal-sharing-meta');
  if (!metaElement) return;
  const meta = JSON.parse(metaElement.textContent);
  const canonicalOrigin = new URL(meta.url).origin;
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const toast = document.createElement('div');
  toast.className = 'portal-copy-toast';
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');
  toast.hidden = true;
  document.body.append(toast);
  let toastTimer;
  function notify(message) {
    toast.textContent = message;
    toast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toast.hidden = true; }, 3500);
  }
  function fallback(text, html) {
    const previous = document.activeElement;
    const area = document.createElement('textarea');
    area.value = text;
    area.className = 'portal-clipboard-area';
    area.setAttribute('readonly', '');
    document.body.append(area);
    const onCopy = event => {
      event.clipboardData.setData('text/plain', text);
      event.clipboardData.setData('text/html', html);
      event.preventDefault();
    };
    document.addEventListener('copy', onCopy);
    area.focus();
    area.select();
    area.setSelectionRange(0, text.length);
    const copied = document.execCommand('copy');
    document.removeEventListener('copy', onCopy);
    area.remove();
    previous?.focus();
    if (!copied) throw new Error('Clipboard unavailable');
  }
  async function copy(title, address, button) {
    const url = new URL(address, canonicalOrigin);
    if (url.origin !== canonicalOrigin) return;
    const text = title + '\n' + url.href;
    const html = '<a href="' + escape(url.href) + '">' + escape(title) + '</a>';
    button.disabled = true;
    try {
      if (navigator.clipboard?.write && window.ClipboardItem) {
        try {
          await navigator.clipboard.write([new ClipboardItem({
            'text/plain': new Blob([text], {type: 'text/plain'}),
            'text/html': new Blob([html], {type: 'text/html'})
          })]);
        } catch (_) {
          if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(text);
          else fallback(text, html);
        }
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else fallback(text, html);
      const old = button.textContent;
      button.textContent = 'تم النسخ';
      notify('تم نسخ: ' + title);
      setTimeout(() => { button.textContent = old; }, 2000);
    } catch (_) {
      notify('تعذّر النسخ التلقائي. يمكنك نسخ عنوان التقرير من شريط المتصفح.');
    } finally { button.disabled = false; }
  }
  document.querySelectorAll('.works > a.work').forEach(link => {
    const wrapper = document.createElement('article');
    wrapper.className = 'portal-site';
    link.replaceWith(wrapper);
    wrapper.append(link);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'portal-copy portal-site-copy';
    button.dataset.reportTitle = link.querySelector('h2')?.textContent.trim() || link.textContent.trim();
    button.dataset.reportUrl = link.getAttribute('href');
    button.textContent = 'نسخ رابط الموقع';
    wrapper.append(button);
  });
  const pageButton = document.createElement('button');
  pageButton.type = 'button';
  pageButton.className = 'portal-copy portal-page-copy';
  pageButton.dataset.reportTitle = meta.title;
  pageButton.dataset.reportUrl = meta.url;
  pageButton.textContent = meta.portal ? 'نسخ رابط البوابة' : 'نسخ رابط التقرير';
  document.body.append(pageButton);
  document.querySelectorAll('.portal-copy[data-report-title]').forEach(button => {
    button.addEventListener('click', () => copy(button.dataset.reportTitle, button.dataset.reportUrl, button));
  });
})();
