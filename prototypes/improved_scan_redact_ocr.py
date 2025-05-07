#!/usr/bin/env python3
"""
Improved Form Scanner using hp-scan for HP scanners and scanimage for others

This script uses the appropriate scanning tools based on detected scanner type:
- hp-scan for HP scanners
- scanimage for other scanners

Requirements:
- sane-utils (for scanimage command)
- hplip (for hp-scan command, needed for HP scanners)
- pillow (for image processing)
- pytesseract (for OCR)
- pdf2image (for PDF processing)
- reportlab (for creating PDFs)
- tesseract-ocr (system package)

Install with:
    sudo apt-get install sane sane-utils tesseract-ocr hplip
    pip install pillow pytesseract pdf2image reportlab
"""

import os
import sys
import subprocess
import datetime
import argparse
import pytesseract
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_path
from pathlib import Path

class FormScanner:
    def __init__(self):
        """Initialize the scanner application."""
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.create_directories()
        self.is_hp_scanner = False
        self.hp_device_uri = None
        
        # First, check if we have an HP scanner
        try:
            print("Checking for HP scanners...")
            result = subprocess.run(['hp-probe', '-b', 'scan'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode == 0 and "SANE" in result.stdout:
                self.is_hp_scanner = True
                # Parse device URI from hp-probe output
                for line in result.stdout.split('\n'):
                    if "Device URI" in line:
                        self.hp_device_uri = line.split("Device URI: ")[1].strip()
                        print(f"Found HP scanner: {self.hp_device_uri}")
                        break
        except FileNotFoundError:
            print("HP tools not found. Will try using standard SANE tools.")
        
        # If HP scanner not found or hp-probe not available, try standard SANE
        if not self.is_hp_scanner:
            # Check if scanimage is available
            try:
                result = subprocess.run(['scanimage', '-V'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if result.returncode != 0:
                    print("Error: scanimage command not found. Please install sane-utils.")
                    sys.exit(1)
            except FileNotFoundError:
                print("Error: scanimage command not found. Please install sane-utils.")
                sys.exit(1)
            
            # List available scanners
            print("Checking for available scanners...")
            try:
                result = subprocess.run(['scanimage', '-L'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if "No scanners were identified" in result.stdout or "No scanners were identified" in result.stderr:
                    print("No scanners found. Please connect a scanner and try again.")
                    sys.exit(1)
                
                # Parse scanner list
                self.devices = []
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('device'):
                        device_id = line.split("'")[1] if "'" in line else line.split("device ")[1].strip()
                        self.devices.append(device_id)
                
                # If HP scanner is detected now, mark it as such
                for device in self.devices:
                    if "HP" in device or "Hewlett-Packard" in device:
                        print("HP scanner detected through SANE.")
                        self.is_hp_scanner = True
                        # Keep using scanimage in this case but note it's an HP

                # If no devices were parsed but output wasn't empty, try the exact device string
                if not self.devices and result.stdout.strip():
                    self.devices = [result.stdout.strip()]
                
                if not self.devices:
                    print("No scanners found. Please connect a scanner and try again.")
                    sys.exit(1)
                
                print("Available scanners:")
                for i, device in enumerate(self.devices):
                    print(f"{i+1}. {device}")
                
                device_num = 0
                if len(self.devices) > 1:
                    while True:
                        try:
                            device_num = int(input("Select scanner (number): ")) - 1
                            if 0 <= device_num < len(self.devices):
                                break
                            print("Invalid selection. Please try again.")
                        except ValueError:
                            print("Please enter a number.")
                
                self.scanner_id = self.devices[device_num]
                print(f"Using scanner: {self.scanner_id}")
                
                # Check for HP scanner in scanner ID
                if "HP" in self.scanner_id or "Hewlett-Packard" in self.scanner_id:
                    self.is_hp_scanner = True
                
                # Check if duplex scanning is available
                self.duplex_available = False
                try:
                    result = subprocess.run(['scanimage', '--help', '-d', self.scanner_id], 
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    if 'duplex' in result.stdout.lower() or 'adf' in result.stdout.lower():
                        self.duplex_available = True
                        print("Duplex scanning may be available on this device!")
                    else:
                        print("Warning: Duplex scanning does not appear to be available on this device.")
                        print("You will need to scan front and back pages separately.")
                except Exception as e:
                    print(f"Warning: Could not determine if duplex scanning is available: {e}")
                    print("Assuming single-sided scanning only.")
            except Exception as e:
                print(f"Error checking scanners: {e}")
                sys.exit(1)
        
        # For HP scanners, check for duplex capability with HP tools
        if self.is_hp_scanner:
            print("Checking HP scanner capabilities...")
            try:
                # Try to detect if duplex is available for HP scanner
                if self.hp_device_uri:
                    result = subprocess.run(['hp-scan', '-l', '-d', self.hp_device_uri], 
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                else:
                    result = subprocess.run(['hp-scan', '-l'], 
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if 'duplex' in result.stdout.lower() or 'adf' in result.stdout.lower():
                    self.duplex_available = True
                    print("HP scanner with duplex/ADF capability detected!")
                else:
                    self.duplex_available = False
                    print("This HP scanner does not appear to have duplex capability.")
            except Exception as e:
                print(f"Warning: Could not determine HP scanner capabilities: {e}")
                print("Will assume duplex is not available.")
                self.duplex_available = False
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = ["./Scans", "./Redactions", "./OCR"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def get_form_info(self):
        """Get form information from the user."""
        while True:
            self.wid = input("Enter WID (10-digit student number): ")
            if len(self.wid) == 10 and self.wid.isdigit():
                break
            print("WID must be a 10-digit number. Please try again.")
        
        while True:
            form_type = input("Enter Form Type (2 or 3): ")
            if form_type in ['2', '3']:
                self.form_type = form_type
                break
            print("Form Type must be either 2 or 3. Please try again.")
        
        # Determine scanning mode
        if self.duplex_available:
            while True:
                mode = input("Do you want to attempt duplex scanning? (y/n): ").lower()
                if mode in ['y', 'n']:
                    self.use_duplex = (mode == 'y')
                    break
                print("Please enter 'y' for yes or 'n' for no.")
        else:
            self.use_duplex = False
            
        # Get number of forms to scan
        while True:
            try:
                self.num_forms = int(input("How many forms to scan (total count, including front/back)? "))
                if self.num_forms > 0:
                    break
                print("Please enter a positive number.")
            except ValueError:
                print("Please enter a number.")

    def scan_page_with_hp_scan(self, output_path, is_duplex=False):
        """Scan a page using hp-scan for HP scanners."""
        try:
            # Set up basic command
            cmd = ['hp-scan', '--mode=color', '--resolution=300']
            
            # Add device URI if we have it
            if self.hp_device_uri:
                cmd.extend(['-d', self.hp_device_uri])
            
            # Add duplex option if requested
            if is_duplex:
                cmd.append('--duplex')
            
            # Add output file (PNG format)
            cmd.extend(['--file=' + output_path])
            
            # Execute command
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                print(f"Error scanning with hp-scan: {result.stderr}")
                return False
            
            return os.path.exists(output_path)
        except Exception as e:
            print(f"Error during HP scanning: {e}")
            return False

    def scan_page_with_scanimage(self, output_path, is_duplex=False):
        """Scan a single page using scanimage."""
        try:
            cmd = [
                'scanimage',
                '--progress',
                '-d', self.scanner_id,
                '--format=png',
                '--resolution=300',
                '--mode=Color'
            ]
            
            # Add duplex option if requested
            if is_duplex:
                cmd.append('--source=ADF Duplex')
            
            # Add output file
            cmd.extend(['--output-file', output_path])
            
            # Execute command
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                print(f"Error scanning: {result.stderr}")
                return False
            
            return os.path.exists(output_path)
        except Exception as e:
            print(f"Error during scanning: {e}")
            return False

    def scan_page(self, output_path, is_duplex=False):
        """Scan a page using the appropriate method based on scanner type."""
        if self.is_hp_scanner:
            return self.scan_page_with_hp_scan(output_path, is_duplex)
        else:
            return self.scan_page_with_scanimage(output_path, is_duplex)

    def scan_documents(self):
        """Scan documents and save them to the Scans directory."""
        scanned_files = []
        
        for form_num in range(1, self.num_forms + 1):
            print(f"\nPreparing to scan form {form_num} of {self.num_forms}")
            
            if self.use_duplex:
                # Try duplex scanning (front and back at once)
                input("Place the form in the scanner and press Enter to scan both sides...")
                
                # For HP scanners with duplex, we can scan both sides at once with hp-scan
                if self.is_hp_scanner:
                    filename_front = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_front.png"
                    filename_back = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_back.png"
                    
                    # Scan with duplex mode
                    if self.scan_page(filename_front, is_duplex=True):
                        scanned_files.append(filename_front)
                        print(f"Front saved to: {filename_front}")
                        
                        # For HP scanners, duplex scanning might save a different file for back
                        # We may need to scan the back separately or move the second page
                        input("Place the BACK of the form in the scanner and press Enter...")
                        if self.scan_page(filename_back):
                            scanned_files.append(filename_back)
                            print(f"Back saved to: {filename_back}")
                        else:
                            print("Failed to scan back page.")
                    else:
                        print("Failed to scan front page or duplex scanning failed.")
                        # Fall back to single-sided scanning
                        self.use_duplex = False
                        # Recursively try again with single-sided mode
                        return self.scan_documents()
                else:
                    # For non-HP scanners, try regular duplex scanning with scanimage
                    filename_front = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_front.png"
                    if self.scan_page(filename_front, is_duplex=True):
                        scanned_files.append(filename_front)
                        print(f"Front saved to: {filename_front}")
                        
                        # We need to handle the back page separately
                        filename_back = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_back.png"
                        input("Place the BACK of the form in the scanner and press Enter...")
                        if self.scan_page(filename_back):
                            scanned_files.append(filename_back)
                            print(f"Back saved to: {filename_back}")
                        else:
                            print("Failed to scan back page.")
                    else:
                        print("Failed to scan with duplex mode. Falling back to single-sided scanning.")
                        self.use_duplex = False
                        # Try again with simplex mode
                        return self.scan_documents()
            else:
                # Single-sided scanning
                # Scan front
                input("Place the FRONT of the form in the scanner and press Enter...")
                filename_front = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_front.png"
                if self.scan_page(filename_front):
                    scanned_files.append(filename_front)
                    print(f"Front saved to: {filename_front}")
                else:
                    print("Failed to scan front page.")
                    continue
                
                # Scan back
                input("Place the BACK of the form in the scanner and press Enter...")
                filename_back = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_back.png"
                if self.scan_page(filename_back):
                    scanned_files.append(filename_back)
                    print(f"Back saved to: {filename_back}")
                else:
                    print("Failed to scan back page.")
        
        return scanned_files

    def apply_redactions(self, scanned_files):
        """Apply redaction overlays to scanned images."""
        redacted_files = []
        
        # Check if redaction overlays exist
        front_overlay_path = f"./redaction-overlays/Form-{self.form_type}-front.png"
        back_overlay_path = f"./redaction-overlays/Form-{self.form_type}-back.png"
        
        if not os.path.exists(front_overlay_path) or not os.path.exists(back_overlay_path):
            print(f"Error: Redaction overlays not found at {front_overlay_path} or {back_overlay_path}")
            return []
        
        front_overlay = Image.open(front_overlay_path).convert("RGBA")
        back_overlay = Image.open(back_overlay_path).convert("RGBA")
        
        for i, scan_path in enumerate(scanned_files):
            try:
                scan = Image.open(scan_path).convert("RGBA")
                
                # Determine if this is a front or back page
                is_front = "_front.png" in scan_path
                overlay = front_overlay if is_front else back_overlay
                
                # Resize overlay to match scan dimensions if needed
                if scan.size != overlay.size:
                    overlay = overlay.resize(scan.size)
                
                # Composite the scan and the overlay
                redacted = Image.alpha_composite(scan, overlay)
                
                # Save the redacted image
                redacted_path = scan_path.replace("./Scans/", "./Redactions/REDACTED_")
                redacted.convert("RGB").save(redacted_path)
                redacted_files.append(redacted_path)
                print(f"Redacted image saved to: {redacted_path}")
                
            except Exception as e:
                print(f"Error applying redaction to {scan_path}: {e}")
        
        return redacted_files

    def perform_ocr(self, redacted_files):
        """Perform OCR on redacted files and save as text and PDF."""
        for redacted_path in redacted_files:
            try:
                # Extract text using Tesseract
                image = Image.open(redacted_path)
                text = pytesseract.image_to_string(image)
                
                # Save as plain text
                text_path = redacted_path.replace("./Redactions/REDACTED_", "./OCR/OCR_").replace(".png", ".txt")
                with open(text_path, "w") as f:
                    f.write(text)
                print(f"OCR text saved to: {text_path}")
                
                # Create searchable PDF
                pdf_path = text_path.replace(".txt", ".pdf")
                
                # Create a PDF with an image layer
                c = canvas.Canvas(pdf_path, pagesize=letter)
                width, height = letter
                c.drawImage(redacted_path, 0, 0, width, height)
                c.save()
                
                print(f"OCR PDF saved to: {pdf_path}")
                
            except Exception as e:
                print(f"Error performing OCR on {redacted_path}: {e}")

    def process(self):
        """Run the complete scanning, redaction, and OCR process."""
        print("=== Form Scanner, Redactor, and OCR Tool ===")
        
        self.get_form_info()
        scanned_files = self.scan_documents()
        
        if scanned_files:
            print("\n=== Applying Redactions ===")
            redacted_files = self.apply_redactions(scanned_files)
            
            if redacted_files:
                print("\n=== Performing OCR ===")
                self.perform_ocr(redacted_files)
                
                print("\n=== Process Complete ===")
                print(f"Scanned files are in: ./Scans/")
                print(f"Redacted files are in: ./Redactions/")
                print(f"OCR results are in: ./OCR/")
            else:
                print("Redaction failed. OCR was not performed.")
        else:
            print("No files were scanned. Process aborted.")

def main():
    """Main entry point for the script."""
    scanner = FormScanner()
    scanner.process()

if __name__ == "__main__":
    main()
