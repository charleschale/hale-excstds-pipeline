const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const REPORT_HTML = '/sessions/focused-hopeful-franklin/mnt/Exc Stds/_reports/Houston_Megan_hiring_report.html';
const OUTPUT_PDF  = '/sessions/focused-hopeful-franklin/mnt/Exc Stds/_reports/Houston_Megan_hiring_report_v11.pdf';
const CHROME_BIN  = '/sessions/focused-hopeful-franklin/.cache/puppeteer/chrome/linux-121.0.6167.85/chrome-linux64/chrome';
const HEADER_TEXT = 'Hale Global Success Diagnostics \u00b7 Excellence Standards Hiring Report \u00b7 Megan Houston';

(async () => {
  let browser;
  try {
    console.log('Launching Chrome at ' + CHROME_BIN);
    browser = await puppeteer.launch({
      headless: 'new',
      executablePath: CHROME_BIN,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 1600 });
    const pageErrors = [];
    page.on('pageerror', e => { pageErrors.push(String(e)); console.error('Page error:', e); });

    console.log('Loading HTML via file://...');
    await page.goto('file://' + REPORT_HTML, { waitUntil: 'networkidle0', timeout: 60000 });

    await page.addStyleTag({ content: `
      p, li { orphans: 3 !important; widows: 3 !important; break-inside: avoid !important; page-break-inside: avoid !important; }
      /* Small atomic units — never split */
      .callout, .bucket, .probe-card, .award-card, .board-role-card,
      .axis-card, .concern-card, .metric-card,
      .l2-row, .timeline-block, .timeline-row, .practice-fuel,
      .dimension-row, .flag-chip, .scorecard-row,
      .probe, .concern, .wiring-row, .htl-item,
      .practice-item, .concern-item, .legend-item {
        break-inside: avoid !important; page-break-inside: avoid !important;
      }
      /* Role-Fit and Concerns boxes: self-contained 2-column content blocks small enough
         to fit one page — keep whole so the title stays attached to the columns. */
      .role-fit-box, .concerns-box {
        break-inside: avoid !important; page-break-inside: avoid !important;
      }
      /* Sections too tall to keep whole — let them break; paragraph-level keep-with-next
         + atomic children handle the seams. */
      .section, .practice-section, .fingerprint, .metrics, .header,
      .wiring-panel, .alignment-grid, .callouts-pair, .dist-chart,
      .ma-section, .career-timeline, .timeline-group,
      .three-axes, .concerns, .interview-probes, .wiring-fit,
      .probes-section, .probes-grid {
        break-inside: auto !important; page-break-inside: auto !important;
      }
      svg { break-inside: auto !important; page-break-inside: auto !important; }
      svg.icon, .flag-icon svg, .metric-card svg { break-inside: avoid !important; page-break-inside: avoid !important; }
      /* Headers keep-with-next — both h-tags AND div-class titles (template uses both). */
      h1,h2,h3,h4,h5,h6,
      .section-title,.subsection-title,.practice-subsection-hdr,.practice-subtitle,
      .bucket-pill,.card-title,.practice-item-title,.axis-title,.concern-title,.probe-title,
      .probes-title,.role-fit-col-label,
      .role-fit-box h3, .concerns-box h3 {
        break-after: avoid !important; page-break-after: avoid !important;
      }
      /* Pair the title with the FIRST child of the next block — seams never strand. */
      .probes-title + .probes-grid,
      .role-fit-box h3 + .role-fit-seat,
      .role-fit-seat + .role-fit-grid,
      .concerns-box h3 + .concern-item,
      .section-title + .timeline,
      .section-title + canvas,
      .section-title + p {
        break-before: avoid !important; page-break-before: avoid !important;
      }
      .section { break-before: auto !important; page-break-before: auto !important; }
      canvas { max-width: 100% !important; height: auto !important; }
    ` });

    await new Promise(r => setTimeout(r, 1800));

    const canvasCheck = await page.evaluate(() => {
      const cv = document.querySelectorAll('canvas');
      const r = {};
      cv.forEach((c, i) => {
        try {
          const ctx = c.getContext('2d');
          const w = Math.max(1, Math.min(c.width, 300));
          const h = Math.max(1, Math.min(c.height, 300));
          const d = ctx.getImageData(0, 0, w, h).data;
          r[c.id || ('canvas_'+i)] = d.some(v => v > 0);
        } catch (e) { r[c.id || ('canvas_'+i)] = 'ERR ' + e.message; }
      });
      return r;
    });
    console.log('Canvas render check:', canvasCheck);
    if (pageErrors.length > 0) {
      console.error('ABORT pageerrors:', pageErrors);
      process.exit(2);
    }

    console.log('Generating 11x17 Tabloid PDF...');
    await page.pdf({
      path: OUTPUT_PDF,
      width: '11in', height: '17in',
      margin: { top: '0.6in', right: '0.6in', bottom: '0.55in', left: '0.6in' },
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: '<div style="width:100%; font-size:9px; color:#999; text-align:right; padding:8px 24px 0 0; font-family:Helvetica, Arial, sans-serif;">' + HEADER_TEXT + '</div>',
      footerTemplate: '<div style="width:100%; font-size:9px; color:#999; text-align:center; padding:0 0 8px 0; font-family:Helvetica, Arial, sans-serif;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>'
    });

    const sz = fs.statSync(OUTPUT_PDF).size;
    console.log('SUCCESS: ' + OUTPUT_PDF);
    console.log('Size: ' + (sz/1024).toFixed(1) + ' KB');
    await browser.close();
    process.exit(0);
  } catch (e) {
    console.error('ERR:', e);
    if (browser) await browser.close();
    process.exit(1);
  }
})();
