/**
 * PDF Renderer for Jody Bender Coaching Guide
 * Uses Puppeteer to render the HTML to PDF at 11x17 Tabloid (Meyrath-standard format).
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

const REPORT_HTML = path.join(__dirname, '..', '..', '_reports', 'Bender_Jody_coaching_guide.html');
const OUTPUT_PDF = path.join(__dirname, '..', '..', '_reports', 'Bender_Jody_coaching_guide_v7.pdf');
const HEADER_TEXT = 'Hale Global Success Diagnostics \u00b7 Excellence Standards Coaching Guide \u00b7 Jody Bender';

(async () => {
  let browser;
  try {
    console.log('Launching browser...');
    browser = await puppeteer.launch({
      executablePath: '/sessions/focused-hopeful-franklin/.cache/puppeteer/chrome/linux-121.0.6167.85/chrome-linux64/chrome',
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 1600 });
    const pageErrors = [];
    page.on('pageerror', (err) => { pageErrors.push(String(err)); console.error('Page error:', err); });

    console.log('Loading HTML file via file://...');
    const fileUrl = 'file://' + REPORT_HTML;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 60000 });

    // Print CSS — paragraph-level keep-together + keep-with-next on headers
    await page.addStyleTag({ content: [
      'p, li {',
      '  orphans: 3 !important;',
      '  widows: 3 !important;',
      '  break-inside: avoid !important;',
      '  page-break-inside: avoid !important;',
      '}',
      '.callout, .bucket, .probe-card, .award-card, .board-role-card,',
      '.axis-card, .concern-card, .metric-card,',
      '.l2-row, .timeline-block, .timeline-row, .practice-fuel,',
      '.dimension-row, .flag-chip, .scorecard-row,',
      '.probe, .concern, .wiring-row, .htl-item,',
      '.practice-item,',
      '.dist-chart-panel {',
      '  break-inside: avoid !important;',
      '  page-break-inside: avoid !important;',
      '}',
      '.dist-chart-title, .dist-chart-key, .section-title + .dist-chart-key {',
      '  break-after: avoid !important;',
      '  page-break-after: avoid !important;',
      '}',
      '.dist-section {',
      '  break-inside: avoid !important;',
      '  page-break-inside: avoid !important;',
      '}',
      '.section, .practice-section, .fingerprint, .metrics, .header,',
      '.wiring-panel, .alignment-grid, .callouts-pair, .dist-chart,',
      '.ma-section, .career-timeline, .timeline-group,',
      '.three-axes, .concerns, .interview-probes, .wiring-fit {',
      '  break-inside: auto !important;',
      '  page-break-inside: auto !important;',
      '}',
      'svg { break-inside: auto !important; page-break-inside: auto !important; }',
      'svg.icon, .flag-icon svg, .metric-card svg {',
      '  break-inside: avoid !important;',
      '  page-break-inside: avoid !important;',
      '}',
      'h1, h2, h3, h4, h5, h6,',
      '.section-title, .subsection-title, .practice-subsection-hdr,',
      '.practice-header, .practice-subtitle,',
      '.metrics-title, .fingerprint-title,',
      '.bucket-pill, .card-title, .practice-item-title,',
      '.axis-title, .concern-title, .probe-title {',
      '  break-after: avoid !important;',
      '  page-break-after: avoid !important;',
      '}',
      'h2 + p, h3 + p, h4 + p,',
      '.section-title + p, .subsection-title + p,',
      '.practice-subsection-hdr + .practice-item,',
      '.practice-header + .practice-subtitle,',
      '.practice-subtitle + .practice-subsection-hdr,',
      '.metrics-title + .metrics-grid,',
      '.fingerprint-title + p,',
      '.section-title + .timeline,',
      '.section-title + canvas {',
      '  break-before: avoid !important;',
      '  page-break-before: avoid !important;',
      '}',
      '.practice-subsection-hdr,',
      '.practice-subsection-hdr-title,',
      '.practice-subsection-hdr-blurb {',
      '  break-inside: avoid !important;',
      '  page-break-inside: avoid !important;',
      '}',
      '.practice-subsection-hdr-title {',
      '  break-after: avoid !important;',
      '  page-break-after: avoid !important;',
      '}',
      '.section {',
      '  break-before: auto !important;',
      '  page-break-before: auto !important;',
      '}',
      'canvas { max-width: 100% !important; height: auto !important; }'
    ].join('\n') });

    await new Promise(r => setTimeout(r, 1800));

    const canvasCheck = await page.evaluate(() => {
      const canvases = document.querySelectorAll('canvas');
      const results = {};
      canvases.forEach((canvas, idx) => {
        try {
          const ctx = canvas.getContext('2d');
          const w = Math.max(1, Math.min(canvas.width, 300));
          const h = Math.max(1, Math.min(canvas.height, 300));
          const imageData = ctx.getImageData(0, 0, w, h);
          const hasPixels = imageData.data.some((val) => val > 0);
          results[canvas.id || ('canvas_' + idx)] = hasPixels;
        } catch (e) {
          results[canvas.id || ('canvas_' + idx)] = 'ERR: ' + e.message;
        }
      });
      return results;
    });

    console.log('Canvas render check:', canvasCheck);
    if (pageErrors.length > 0) {
      console.error('ABORT: pageerror events fired:', pageErrors);
      process.exit(2);
    }

    console.log('Generating PDF (11x17 Tabloid)...');
    await page.pdf({
      path: OUTPUT_PDF,
      width: '11in',
      height: '17in',
      margin: { top: '0.6in', right: '0.6in', bottom: '0.55in', left: '0.6in' },
      printBackground: true,
      displayHeaderFooter: true,
      headerTemplate: '<div style="width:100%; font-size:9px; color:#999; text-align:right; padding:8px 24px 0 0; font-family:Helvetica, Arial, sans-serif;">' + HEADER_TEXT + '</div>',
      footerTemplate: '<div style="width:100%; font-size:9px; color:#999; text-align:center; padding:0 0 8px 0; font-family:Helvetica, Arial, sans-serif;"><span class="pageNumber"></span> / <span class="totalPages"></span></div>'
    });

    const stats = fs.statSync(OUTPUT_PDF);
    console.log('\nSUCCESS: PDF written to ' + OUTPUT_PDF);
    console.log('Size: ' + (stats.size / 1024).toFixed(1) + ' KB');

    await browser.close();
    process.exit(0);
  } catch (err) {
    console.error('Error during PDF generation:', err);
    if (browser) await browser.close();
    process.exit(1);
  }
})();
