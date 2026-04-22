/**
 * PDF Renderer for Hechler Howard Hiring Report
 * Uses Puppeteer to render the HTML to PDF at 11x17 Tabloid (Meyrath-standard format).
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const REPORT_HTML = path.join(__dirname, '..', '..', '_reports', 'Hechler_Howard_hiring_report.html');
const OUTPUT_PDF = path.join(__dirname, '..', '..', '_reports', 'Hechler_Howard_hiring_report_v5.pdf');
const HEADER_TEXT = 'Hale Global Success Diagnostics \u00b7 Excellence Standards Hiring Report \u00b7 Howard Hechler';

(async () => {
  let browser;
  try {
    console.log('Launching browser...');
    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 1600 });
    page.on('pageerror', (err) => { console.error('Page error:', err); });

    console.log('Loading HTML file via file://...');
    const fileUrl = 'file://' + REPORT_HTML;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 60000 });

    // Print CSS — paragraph-level keep-together + keep-with-next on headers
    // (see skill print/PDF strategy block)
    await page.addStyleTag({ content: `
      p, li {
        orphans: 3 !important;
        widows: 3 !important;
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }
      .callout, .bucket, .probe-card, .award-card, .board-role-card,
      .axis-card, .concern-card, .metric-card,
      .l2-row, .timeline-block, .timeline-row, .practice-fuel,
      .dimension-row, .flag-chip, .scorecard-row,
      .probe, .concern, .wiring-row, .htl-item {
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }
      .section, .practice-section, .fingerprint, .metrics, .header,
      .wiring-panel, .alignment-grid, .callouts-pair, .dist-chart,
      .ma-section, .career-timeline, .timeline-group,
      .three-axes, .concerns, .interview-probes, .wiring-fit {
        break-inside: auto !important;
        page-break-inside: auto !important;
      }
      svg { break-inside: auto !important; page-break-inside: auto !important; }
      svg.icon, .flag-icon svg, .metric-card svg {
        break-inside: avoid !important;
        page-break-inside: avoid !important;
      }
      h1, h2, h3, h4, h5, h6,
      .section-title, .subsection-title, .practice-subsection-hdr,
      .practice-subtitle, .bucket-pill, .card-title, .practice-item-title,
      .axis-title, .concern-title, .probe-title {
        break-after: avoid !important;
        page-break-after: avoid !important;
      }
      h2 + p, h3 + p, h4 + p,
      .section-title + p, .subsection-title + p {
        break-before: avoid !important;
        page-break-before: avoid !important;
      }
      .section {
        break-before: auto !important;
        page-break-before: auto !important;
      }
      canvas { max-width: 100% !important; height: auto !important; }
    ` });

    await new Promise(r => setTimeout(r, 1500));

    const canvasCheck = await page.evaluate(() => {
      const canvases = document.querySelectorAll('canvas');
      const results = {};
      canvases.forEach((canvas, idx) => {
        const ctx = canvas.getContext('2d');
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const hasPixels = imageData.data.some(val => val > 0);
        results[canvas.id || ('canvas_' + idx)] = hasPixels;
      });
      return results;
    });

    console.log('Canvas render check:', canvasCheck);

    console.log('Generating PDF (11x17 Tabloid)...');
    await page.pdf({
      path: OUTPUT_PDF,
      width: '11in',
      height: '17in',
      margin: {
        top: '0.6in',
        right: '0.6in',
        bottom: '0.55in',
        left: '0.6in'
      },
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
