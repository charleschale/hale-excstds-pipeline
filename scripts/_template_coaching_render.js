/**
 * TEMPLATE: Coaching-guide PDF renderer
 *
 * Fork this for the next coaching-guide build. Replace SLUG and CANDIDATE_NAME
 * below; everything else (print-CSS contract, canvas health-check, page setup)
 * is inherited from the shared _print_css.json data file.
 *
 * Source of truth for the print-CSS pagination contract:
 *   _pipeline/scripts/_print_css.json -> "coaching"
 * See METHODOLOGY.md "Coaching-guide print-CSS pagination contract" and
 * QA_CHECKLIST.md Section 11i for the rationale.
 *
 * Run from repo root:
 *   node _pipeline/scripts/render_<slug>_coaching_pdf.js
 */

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');

// =================== EDIT THESE FOR EACH NEW BUILD ===================
const SLUG = 'TODO_lastname_firstname';                  // e.g. 'Bender_Jody'
const CANDIDATE_NAME = 'TODO Candidate Name';            // e.g. 'Jody Bender'
const PDF_VERSION = 'v1';                                 // bump v1, v2, ... per iteration
// =====================================================================

const REPORT_HTML = path.join(__dirname, '..', '..', '_reports', `${SLUG}_coaching_guide.html`);
const OUTPUT_PDF  = path.join(__dirname, '..', '..', '_reports', `${SLUG}_coaching_guide_${PDF_VERSION}.pdf`);
const HEADER_TEXT = `Hale Global Success Diagnostics \u00b7 Excellence Standards Coaching Guide \u00b7 ${CANDIDATE_NAME}`;

// Load shared print-CSS contract from data file (single source of truth)
const PRINT_CSS_PATH = path.join(__dirname, '_print_css.json');
const PRINT_CSS = JSON.parse(fs.readFileSync(PRINT_CSS_PATH, 'utf8')).coaching.join('\n');

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

    console.log(`Loading ${REPORT_HTML} ...`);
    await page.goto('file://' + REPORT_HTML, { waitUntil: 'networkidle0', timeout: 60000 });

    // Apply shared print-CSS contract
    await page.addStyleTag({ content: PRINT_CSS });
    await new Promise(r => setTimeout(r, 1800));

    // Canvas health-check (Section 11i.6) — fail fast if Chart.js lost the buffer
    const canvasCheck = await page.evaluate(() => {
      const results = {};
      document.querySelectorAll('canvas').forEach((canvas, idx) => {
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
    const emptyCanvases = Object.entries(canvasCheck).filter(([_, v]) => v !== true);
    if (emptyCanvases.length > 0) {
      console.error('ABORT: empty canvases:', emptyCanvases);
      process.exit(2);
    }
    if (pageErrors.length > 0) {
      console.error('ABORT: pageerror events:', pageErrors);
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
