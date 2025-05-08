# Privacy Redacting Image Scanning Middleware - Installation & Usage Guide

![PRISM](./resources/PRISM-Logo.png)


This guide will help you set up and use the Scan-to-Redact-to-OCR solution on Ubuntu 24.04.

## Prerequisites

- Ubuntu 24.04
- A compatible USB scanner
- Python 3.x (comes pre-installed on Ubuntu 24.04)

## Installation

1. **Install system dependencies:**

   ```bash
   sudo apt-get update
   sudo apt-get install -y sane sane-utils tesseract-ocr python3-pip python3-venv build-essential libsane-dev
   ```

   The `build-essential` and `libsane-dev` packages are required for compiling the `python-sane` package.

   For HP scanners, also install:
   ```bash
   sudo apt-get install hplip
   ```

2. **Create a virtual environment (recommended):**

   ```bash
   python3 -m venv scan-env
   source scan-env/bin/activate
   ```

3. **Install required Python packages:**

   For the main script (Option 1):
   ```bash
   pip install python-sane pillow pytesseract pdf2image reportlab
   ```

   For the alternative script (Option 2, no compilation required):
   ```bash
   pip install pillow pytesseract pdf2image reportlab
   ```

   For the HP-optimized script (Option 3):
   ```bash
   pip install pillow pytesseract pdf2image reportlab
   ```

4. **Verify scanner detection:**

   ```bash
   scanimage -L
   ```

   This should list your scanner. If not, check that it's properly connected.

   Example Detection:
   ```
   $ scanimage -L
   
   device `escl:https://192.168.1.24:443' is a Epson ET-4810 Series platen,adf scanner
   device `epson2:net:192.168.1.24' is a Epson PID flatbed scanner
   device `airscan:e0:EPSON ET-4810 Series' is a eSCL EPSON ET-4810 Series ip=192.168.1.24
   ```

   For HP scanners, you can also use:
   ```bash
   hp-probe
   ```

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

You have three options for running the scanner script:

### Option 1: Using the python-sane based script (requires compilation)

1. **Make the script executable:**

   ```bash
   chmod +x scan_redact_ocr.py
   ```

2. **Run the script:**

   ```bash
   ./scan_redact_ocr.py
   ```

### Option 2: Using the scanimage-based alternative (no compilation required)

If you encounter issues with python-sane or prefer not to install build tools, use this alternative:

1. **Make the alternative script executable:**

   ```bash
   chmod +x alternative_scanner.py
   ```

2. **Run the alternative script:**

   ```bash
   ./alternative_scanner.py
   ```

This alternative uses the command-line `scanimage` tool instead of the python-sane library and requires fewer dependencies.

### Option 3: Using the HP-optimized script for HP scanners

If you have an HP scanner (like the HP ScanJet Flow 7000 s3), use this script which utilizes HP's native tools:

1. **Make sure you have HPLIP tools installed:**

   ```bash
   sudo apt-get install hplip
   ```

2. **Setup your HP scanner (if not already configured):**

   ```bash
   hp-setup
   ```

3. **Make the HP-optimized script executable:**

   ```bash
   chmod +x improved_scan_redact_ocr.py
   ```

4. **Run the HP-optimized script:**

   ```bash
   ./improved_scan_redact_ocr.py
   ```

This script uses `hp-scan` instead of `scanimage` and has better support for HP scanner features like duplex scanning.

## Using the Scripts

1. **Follow the prompts:**
   - Enter the 10-digit WID (student number)
   - Select Form Type:
     - 0 (Skip/None) for Memo documents with no redaction
     - 2 or 3 for standard forms with redaction   - Choose duplex scanning if available
   - Specify how many forms to scan
   - Follow scanning instructions for each form

## Output Files

The script will generate files with the following naming convention:

For standard forms (type 2 or 3):
- **Scanned images:**
  `./Scans/YYYY-MM-DD_Form#-WID_form#_[front|back].png`

- **Redacted images:**
  `./Redactions/REDACTED_YYYY-MM-DD_Form#-WID_form#_[front|back].png`

For all form types including Memo documents (type 0):
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

- **HP Scanner "Operation not supported" error:** Use the HP-optimized script (Option 3) which uses native HP tools instead of generic SANE interfaces.

- **Image alignment issues:** Make sure your redaction overlays match the exact dimensions of your scanned forms (8.5" x 11").

## Additional Notes

- The script sets the scanner to 300 DPI and color mode for best results.
- Each form has both front and back pages scanned, even with single-sided scanning.
- The script verifies if duplex scanning is available before offering the option.
- Redacted files retain the original image quality while protecting privacy data.
- OCR results are provided in both text and searchable PDF formats.

## ERRORs - Protips

### 1. Ensure you are in the Python env!

If you See:
```
Traceback (most recent call last):
  File "/home/<USER>/PRISM/./PRISM.py", line 23, in <module>
    import sane
ModuleNotFoundError: No module named 'sane'
```

THEN -- ensure you run: `source scan-env/bin/activate`

### 2. Cannot locate scanner (when re-using the app)

THIS IS AS-IS Software! -- With that, there's a sane-scanner interface, or I/O disconnect bug. SO... "turn it off, and on again" has worked for my scanner to reuse the app!

### 3. HP Scanner Issues

If you have an HP scanner (like the HP ScanJet) and encounter errors with the regular scripts:

1. Make sure HPLIP is installed: `sudo apt-get install hplip`
2. Run HP setup utility: `hp-setup` 
3. Use the HP-optimized script (Option 3): `./improved_scan_redact_ocr.py`

This uses HP's native scanning tools which provide better support for HP hardware features.
