"""PDF Renderer for Hechler Howard Hiring Report using pdfkit + wkhtmltopdf.

Run from repo root:
    python _pipeline/scripts/make_pdf_hechler.py

Outputs to:
    _reports/Hechler_Howard_hiring_report.pdf
"""

from pathlib import Path
import sys
import pdfkit

ROOT = Path(__file__).resolve().parents[2]
REPORT_HTML = ROOT / '_reports' / 'Hechler_Howard_hiring_report.html'
OUTPUT_PDF = ROOT / '_reports' / 'Hechler_Howard_hiring_report.pdf'

def main():
    if not REPORT_HTML.exists():
        print(f"ERROR: {REPORT_HTML} not found")
        sys.exit(1)

    print(f"Loading HTML from {REPORT_HTML}")
    print("Rendering PDF with wkhtmltopdf...")

    try:
        options = {
            'page-size': 'Letter',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'print-media-type': None,
            'enable-local-file-access': None,
        }

        pdfkit.from_file(str(REPORT_HTML), str(OUTPUT_PDF), options=options)

        if OUTPUT_PDF.exists():
            size_kb = OUTPUT_PDF.stat().st_size / 1024
            print(f"\nSUCCESS: PDF written to {OUTPUT_PDF}")
            print(f"Size: {size_kb:.1f} KB")

            if size_kb < 500:
                print("WARNING: PDF file size is small (<500KB). May indicate rendering issue.")
            else:
                print("File size OK.")
        else:
            print("ERROR: PDF was not created")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR during PDF generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
