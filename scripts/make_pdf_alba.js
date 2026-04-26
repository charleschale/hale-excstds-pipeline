/**
 * PDF Renderer for Alba Quintas Núñez Coaching Guide
 * Uses Puppeteer to render the HTML to PDF at 11x17 Tabloid (Meyrath/Cohen-standard format).
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

const REPORT_HTML = path.join(__dirname, '..', '..', '_reports', 'Quintas-Nunez_Alba_coaching_guide.html');
// Allow PDF override via CLI: `node make_pdf_alba.js v2` -> ..._coaching_guide_v2.pdf
const SUFFIX = process.argv[2] ? '_' + process.argv[2] : '';
const OUTPUT_PDF = path.join(__dirname, '..', '..', '_reports', 'Quintas-Nunez_Alba_coaching_guide' + SUFFIX + '.pdf');
const HEADER_TEXT = 'Hale Global Success Diagnostics \u00b7 Excellence Standards Coaching Guide \u00b7 Alba Quintas N\u00fa\u00f1ez';

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
    const pageErrors = [];
    page.on('pageerror', (err) => { pageErrors.push(String(err)); console.error('Page error:', err); });

    console.log('Loading HTML file via file://...');
    const fileUrl = 'file://' + REPORT_HTML;
    await page.goto(fileUrl, { waitUntil: 'networkidle0', timeout: 60000 });

    // Print CSS — paragraph-level keep-together + keep-with-next on headers
    // (see SKILL.md print/PDF strategy block — "keep-with-next, not container-atomicity")
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
      .probe, .concern, .wiring-row, .htl-item,
      .practice-item {
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
          const hasPixels = imageData.data.some(val => val > 0);
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
process.exit(0);
  } catch (err) {
    console.error('Error during PDF generation:', err);
    if (browser) await browser.close();
    process.exit(1);
  }
})();
