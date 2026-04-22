const puppeteer = require('puppeteer');
const path = require('path');
const REPORT_HTML = path.join('/sessions/beautiful-pensive-einstein/mnt/Exc Stds', '_reports', 'Cohen_Matthew_hiring_report.html');
(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  page.on('console', msg => console.log('C:', msg.type(), msg.text().slice(0,600)));
  page.on('pageerror', err => console.log('PE:', String(err).slice(0,600)));
  page.on('error', err => console.log('ERR:', String(err).slice(0,600)));
  await page.setViewport({ width: 1200, height: 1600 });
  await page.goto('file://' + REPORT_HTML, { waitUntil: 'networkidle0', timeout: 60000 });
  await new Promise(r => setTimeout(r, 2500));
  const probe = await page.evaluate(() => {
    const scripts = document.querySelectorAll('script');
    const last = scripts[scripts.length - 1];
    const code = last.textContent;
    try {
      new Function(code)();
      return 'OK';
    } catch (e) {
      return 'EXEC_ERR: ' + e.message + ' at lineSubstring[:200]=' + code.slice(0,200);
    }
  });
  console.log('EXEC PROBE:', probe);
  await browser.close();
})();
