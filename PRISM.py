#!/usr/bin/env python3
"""
Privacy Act Form Scanner, Redactor, and OCR Tool

This script scans forms, applies redaction overlays, and performs OCR on the results.
It handles both single and duplex scanning based on available hardware capabilities.

Requirements:
- python-sane (for scanning)
- pillow (for image processing)
- pytesseract (for OCR)
- pdf2image (for PDF processing)
- reportlab (for creating PDFs)
- tesseract-ocr (system package)

Install with:
    sudo apt-get install sane sane-utils tesseract-ocr
    pip install python-sane pillow pytesseract pdf2image reportlab
"""

import os
import sys
import sane
import re
import datetime
import argparse
import pytesseract
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_path
from pathlib import Path

def print_prism_banner():
    banner = r"""
    ██████╗ ██████╗ ██╗███████╗███╗   ███╗
    ██╔══██╗██╔══██╗██║██╔════╝████╗ ████║
    ██████╔╝██████╔╝██║███████╗██╔████╔██║
    ██╔═══╝ ██╔══██╗██║╚════██║██║╚██╔╝██║
    ██║     ██║  ██║██║███████║██║ ╚═╝ ██║
    ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝
    
    Privacy Redacting Image Scanning Middleware
    """
    print(banner)

class FormScanner:
    def __init__(self):
        """Initialize the scanner application."""
        # Display the PRISM banner
        print_prism_banner()
        
        self.today = datetime.datetime.now().strftime("%Y-%m-%d")
        self.create_directories()
        self.wid = ""
        self.form_type = ""
        self.scan_counter = self.get_next_scan_number()
        self.perform_ocr = True
        
        # Initialize SANE
        print("\n" + "="*70)
        print("Initializing scanner...")
        print("="*70 + "\n")
        
        sane.init()
        self.devices = sane.get_devices()
        if not self.devices:
            print("No scanners found. Please connect a scanner and try again.")
            sys.exit(1)
        
        print("Available scanners:")
        for i, device in enumerate(self.devices):
            print(f"{i+1}. {device[0]} - {device[1]}")
        
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
        
        try:
            self.scanner = sane.open(self.devices[device_num][0])
            print(f"Using scanner: {self.devices[device_num][1]}")
        except Exception as e:
            print(f"Error opening scanner: {e}")
            print("This scanner may not be compatible with python-sane.")
            print("Try using the alternative_scanner.py script instead.")
            sys.exit(1)

        # Check if duplex scanning is available
        self.duplex_available = False
        try:
            options = self.scanner.get_options()
            for option in options:
                if 'duplex' in option.name.lower():
                    self.duplex_available = True
                    print("Duplex scanning is available on this device!")
                    break
            
            if not self.duplex_available:
                print("Warning: Duplex scanning does not appear to be available on this device.")
                print("You will need to scan front and back pages separately.")
        except Exception as e:
            print(f"Warning: Could not determine if duplex scanning is available: {e}")
            print("Assuming single-sided scanning only.")
    
    def create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = ["./Scans", "./Redactions", "./OCR"]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    def get_next_scan_number(self):
        """Determine the next scan number based on existing files."""
        max_scan_num = 0
        
        # Check existing files in the Scans directory
        scan_dir = "./Scans"
        if os.path.exists(scan_dir):
            today_str = self.today
            scan_pattern = re.compile(rf"{today_str}_Form\d+-\d+_scan(\d+)_[ab]_")
            
            for filename in os.listdir(scan_dir):
                match = scan_pattern.search(filename)
                if match:
                    scan_num = int(match.group(1))
                    if scan_num > max_scan_num:
                        max_scan_num = scan_num
        
        # Start from 1 if no existing files found, otherwise use the next number
        return max_scan_num + 1

    def increment_scan_counter(self):
        """Increment the scan counter after processing a form."""
        self.scan_counter += 1

    def get_filename_base(self):
        """Generate the base filename for the current scan."""
        # Format: YYYY-MM-DD_Form#-WID_scan#
        return f"{self.today}_Form{self.form_type}-{self.wid}_scan{self.scan_counter:02d}"
        # Note: Using :02d to zero-pad the scan number to at least 2 digits

    def setup_initial_preferences(self):
        """Get initial preferences from the user."""
        print("\n" + "="*70)
        print("Setting up preferences...")
        print("="*70 + "\n")
        
        # Ask if OCR is wanted
        while True:
            ocr_choice = input("Do you want to perform OCR on scanned forms? [Y/n]: ").lower()
            if ocr_choice in ['', 'y', 'n']:
                self.perform_ocr = ocr_choice != 'n'
                break
            print("Please enter 'y' for yes or 'n' for no, or press Enter for default (yes).")
        
        print(f"\nOCR processing is {'enabled' if self.perform_ocr else 'disabled'}.")

    def get_form_info(self):
        """Get form information from the user."""
        print("\n" + "-"*70)
        print("Form information")
        print("-"*70 + "\n")
        
        # For WID, allow reusing the previous one
        if self.wid:
            wid_input = input(f"Enter WID (10-digit student number) or press Enter to use [{self.wid}]: ")
            if not wid_input:
                # Keep the existing WID
                pass
            elif len(wid_input) == 10 and wid_input.isdigit():
                self.wid = wid_input
            else:
                while True:
                    wid_input = input("WID must be a 10-digit number. Please try again: ")
                    if len(wid_input) == 10 and wid_input.isdigit():
                        self.wid = wid_input
                        break
        else:
            # First time, require a valid WID
            while True:
                self.wid = input("Enter WID (10-digit student number): ")
                if len(self.wid) == 10 and self.wid.isdigit():
                    break
                print("WID must be a 10-digit number. Please try again.")
        
        # Form type
        while True:
            form_type = input("Enter Form Type (0: Skip/None, 2, or 3): ")
            if form_type in ['0', '2', '3']:
                self.form_type = form_type
                break
            print("Form Type must be 0 (Skip/None), 2, or 3. Please try again.")
        
        # Determine scanning mode
        if self.duplex_available:
            while True:
                mode = input("Use duplex scanning? [Y/n]: ").lower()
                if mode in ['', 'y', 'n']:
                    self.use_duplex = (mode != 'n')
                    break
                print("Please enter 'y' for yes or 'n' for no, or press Enter for default (yes).")
        else:
            self.use_duplex = False

    def configure_scanner(self):
        """Configure scanner settings for form scanning."""
        # Set scanner to color mode
        try:
            self.scanner.mode = 'Color'
        except:
            print("Warning: Could not set color mode. Using default mode.")
        
        # Try to set resolution to 300 DPI
        try:
            self.scanner.resolution = 300
        except:
            print("Warning: Could not set resolution to 300 DPI. Using default resolution.")
        
        # Set paper size to Letter if possible
        try:
            self.scanner.br_x = 215.9  # 8.5 inches in mm
            self.scanner.br_y = 279.4  # 11 inches in mm
        except:
            print("Warning: Could not set paper size to Letter. Using default size.")
        
        # Set duplex mode if available and requested
        if self.use_duplex and self.duplex_available:
            try:
                for option in self.scanner.get_options():
                    if 'duplex' in option.name.lower():
                        setattr(self.scanner, option.name, True)
                        print("Duplex scanning enabled!")
                        break
            except Exception as e:
                print(f"Warning: Could not enable duplex scanning: {e}")
                self.use_duplex = False
                print("Falling back to simplex (single-sided) scanning.")

    def scan_documents(self):
        """Scan a single document (front and back) and save them to the Scans directory."""
        print("\n" + "-"*70)
        print("Scanning document")
        print("-"*70 + "\n")
        
        self.configure_scanner()
        scanned_files = []
        
        # Get the base filename
        base_filename = self.get_filename_base()
        
        if self.use_duplex:
            # In duplex mode, we scan both sides at once
            input("Place the form in the scanner and press Enter to scan both sides...")
            
            try:
                print("Scanning...")
                self.scanner.start()
                image = self.scanner.snap()
                
                # Save front side
                filename_front = f"./Scans/{base_filename}_a_front.png"
                image.save(filename_front)
                scanned_files.append(filename_front)
                print(f"Front saved to: {filename_front}")
                
                # For duplex scanning, we should get a second image automatically
                try:
                    image_back = self.scanner.snap()
                    filename_back = f"./Scans/{base_filename}_b_back.png"
                    image_back.save(filename_back)
                    scanned_files.append(filename_back)
                    print(f"Back saved to: {filename_back}")
                except Exception as e:
                    print(f"Error scanning back side: {e}")
                    print("You may need to scan the back side separately.")
                    
            except Exception as e:
                print(f"Error during scanning: {e}")
                
        else:
            # In simplex mode, we scan front and back separately
            input("Place the FRONT of the form in the scanner and press Enter...")
            
            try:
                print("Scanning front...")
                self.scanner.start()
                image = self.scanner.snap()
                filename_front = f"./Scans/{base_filename}_a_front.png"
                image.save(filename_front)
                scanned_files.append(filename_front)
                print(f"Front saved to: {filename_front}")
            except Exception as e:
                print(f"Error scanning front: {e}")
            
            input("Place the BACK of the form in the scanner and press Enter...")
            
            try:
                print("Scanning back...")
                self.scanner.start()
                image = self.scanner.snap()
                filename_back = f"./Scans/{base_filename}_b_back.png"
                image.save(filename_back)
                scanned_files.append(filename_back)
                print(f"Back saved to: {filename_back}")
            except Exception as e:
                print(f"Error scanning back: {e}")
        
        return scanned_files

    def apply_redactions(self, scanned_files):
        """Apply redaction overlays to scanned images."""
        print("\n" + "-"*70)
        print("Applying redactions")
        print("-"*70 + "\n")
        
        redacted_files = []
        
        # Check if redaction overlays exist
        front_overlay_path = f"./redaction-overlays/Form-{self.form_type}-front.png"
        back_overlay_path = f"./redaction-overlays/Form-{self.form_type}-back.png"
        
        if not os.path.exists(front_overlay_path) or not os.path.exists(back_overlay_path):
            print(f"Error: Redaction overlays not found at {front_overlay_path} or {back_overlay_path}")
            return []
        
        front_overlay = Image.open(front_overlay_path)
        back_overlay = Image.open(back_overlay_path)
        
        for i, scan_path in enumerate(scanned_files):
            try:
                scan = Image.open(scan_path)
                
                # Determine if this is a front or back page
                is_front = "_a_front.png" in scan_path
                overlay = front_overlay if is_front else back_overlay
                
                # Resize overlay to match scan dimensions if needed
                if scan.size != overlay.size:
                    overlay = overlay.resize(scan.size)
                
                # Composite the scan and the overlay
                redacted = Image.alpha_composite(scan.convert("RGBA"), overlay)
                
                # Save the redacted image
                redacted_path = scan_path.replace("./Scans/", "./Redactions/REDACTED_")
                redacted.convert("RGB").save(redacted_path)
                redacted_files.append(redacted_path)
                print(f"Redacted image saved to: {redacted_path}")
                
            except Exception as e:
                print(f"Error applying redaction to {scan_path}: {e}")
        
        return redacted_files

    def perform_ocr_process(self, redacted_files):
        """Perform OCR on redacted files and save as text and PDF."""
        print("\n" + "-"*70)
        print("Performing OCR")
        print("-"*70 + "\n")

        # For Memo documents (form_type = 0), redacted_files actually contains the original scanned files
        # We need to adjust the output path for OCR results
        path_prefix = "./OCR/OCR_"
        path_replace = "./Redactions/REDACTED_" if self.form_type != '0' else "./Scans/"

        # Process each file
        ocr_files = []

        for redacted_path in redacted_files:
            try:
                # Extract text using Tesseract
                image = Image.open(redacted_path)
                text = pytesseract.image_to_string(image)
                
                # Save as plain text
                text_path = redacted_path.replace(path_replace, path_prefix).replace(".png", ".txt")
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
                ocr_files.append(pdf_path)
                
            except Exception as e:
                print(f"Error performing OCR on {redacted_path}: {e}")
        return ocr_files

    def process_single_form(self):
        """Process a single form through scanning, redaction, and optional OCR."""
        self.get_form_info()
        scanned_files = self.scan_documents()

                if self.form_type == '0':
                    # For Memo documents, skip redaction but proceed with OCR if enabled
                    if self.perform_ocr:
                        print("\nSkipping redaction for Memo document.")
                        self.perform_ocr_process(scanned_files)
                    else:
                        # Normal workflow for form types 2 and 3
                        redacted_files = self.apply_redactions(scanned_files)

                    if redacted_files and self.perform_ocr:
                        self.perform_ocr_process(redacted_files)
            return True
        else:
            print("\nNo files were scanned. Process aborted.")
            return False

    def close(self):
        """Safely close the scanner connection."""
        try:
            print("\nSafely closing scanner connection...")
            self.scanner.close()
            sane.exit()
            print("Scanner connection closed successfully.")
        except Exception as e:
            print(f"Warning: Error while closing scanner: {e}")
            print("The scanner may still show as busy. Try disconnecting and reconnecting it.")

    def run(self):
        """Run the complete workflow with the improved process."""
        print("\n" + "="*70)
        print("=== Form Scanner, Redactor, and OCR Tool ===")
        print("="*70 + "\n")
        
        # Get initial preferences (OCR yes/no)
        self.setup_initial_preferences()
        
        # Main processing loop
        continue_scanning = True
        
        while continue_scanning:
            success = self.process_single_form()
            
            if success:
                self.increment_scan_counter()
            
            print("\n" + "-"*70)
            choice = input("Would you like to scan another form? [Y/n]: ").lower()
            continue_scanning = choice != 'n'
            print("-"*70 + "\n")
        
        # Safely close scanner connection before exiting
        self.close()
        
        print("\n" + "="*70)
        print("=== Process Complete ===")
        print(f"Scanned files are in: ./Scans/")
        print(f"Redacted files are in: ./Redactions/")
        if self.perform_ocr:
            print(f"OCR results are in: ./OCR/")
        print("="*70 + "\n")

def main():
    """Main entry point for the script."""
    scanner = FormScanner()
    scanner.run()

if __name__ == "__main__":
    main()
