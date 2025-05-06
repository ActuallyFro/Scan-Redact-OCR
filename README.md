# Form Scanner, Redactor, and OCR - Installation & Usage Guide

This guide will help you set up and use the Scan-to-Redact-to-OCR solution on Ubuntu 24.04.

## Prerequisites

- Ubuntu 24.04
- A compatible USB scanner
- Python 3.x (comes pre-installed on Ubuntu 24.04)

## Installation

1. **Install system dependencies:**

   ```bash
   sudo apt-get update
   sudo apt-get install -y sane sane-utils tesseract-ocr python3-pip python3-venv
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python3 -m venv scan-env
   source scan-env/bin/activate
   ```

3. **Install required Python packages:**

   ```bash
   pip install python-sane pillow pytesseract pdf2image reportlab
   ```

4. **Verify scanner detection:**

   ```bash
   scanimage -L
   ```

   This should list your scanner. If not, check that it's properly connected.

5. **Create directory structure:**

   ```bash
   mkdir -p Scans Redactions OCR redaction-overlays
   ```

6. **Place redaction overlays:**
   Place your redaction overlay files in the `redaction-overlays` directory with the following names:
   - `Form-2-front.png`
   - `Form-2-back.png`
   - `Form-3-front.png`
   - `Form-3-back.png`

   These should be 8.5" x 11" PNG files with transparency where data should show through, and black areas for redaction.

## Running the Script

1. **Make the script executable:**

   ```bash
   chmod +x scan_redact_ocr.py
   ```

2. **Run the script:**

   ```bash
   ./scan_redact_ocr.py
   ```

3. **Follow the prompts:**
   - Enter the 10-digit WID (student number)
   - Select Form Type (2 or 3)
   - Choose duplex scanning if available
   - Specify how many forms to scan
   - Follow scanning instructions for each form

## Output Files

The script will generate files with the following naming convention:

- **Scanned images:**
  `./Scans/YYYY-MM-DD_Form#-WID_form#_[front|back].png`

- **Redacted images:**
  `./Redactions/REDACTED_YYYY-MM-DD_Form#-WID_form#_[front|back].png`

- **OCR text files:**
  `./OCR/OCR_YYYY-MM-DD_Form#-WID_form#_[front|back].txt`

- **OCR searchable PDFs:**
  `./OCR/OCR_YYYY-MM-DD_Form#-WID_form#_[front|back].pdf`

## Troubleshooting

- **Scanner not detected:** Ensure it's properly connected and powered on. You may need to add your user to the 'scanner' group:
  ```bash
  sudo usermod -a -G scanner $USER
  ```
  Log out and back in for changes to take effect.

- **Permission errors:** Ensure you have write permissions for all directories.

- **SANE errors:** Check that your scanner is SANE-compatible. Run `scanimage -L` to verify.

- **Image alignment issues:** Make sure your redaction overlays match the exact dimensions of your scanned forms (8.5" x 11").

## Additional Notes

- The script sets the scanner to 300 DPI and color mode for best results.
- Each form has both front and back pages scanned, even with single-sided scanning.
- The script verifies if duplex scanning is available before offering the option.
- Redacted files retain the original image quality while protecting privacy data.
- OCR results are provided in both text and searchable PDF formats.
