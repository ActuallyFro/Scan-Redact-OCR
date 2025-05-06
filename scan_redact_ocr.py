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
        
        # Initialize SANE
        print("Initializing scanner...")
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
        
        self.scanner = sane.open(self.devices[device_num][0])
        print(f"Using scanner: {self.devices[device_num][1]}")
        
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
                mode = input("Use duplex scanning? (y/n): ").lower()
                if mode in ['y', 'n']:
                    self.use_duplex = (mode == 'y')
                    break
                print("Please enter 'y' for yes or 'n' for no.")
        else:
            self.use_duplex = False
            
        # Get number of forms to scan
        while True:
            try:
                self.num_forms = int(input("How many forms to scan? "))
                if self.num_forms > 0:
                    break
                print("Please enter a positive number.")
            except ValueError:
                print("Please enter a number.")

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
        """Scan documents and save them to the Scans directory."""
        self.configure_scanner()
        scanned_files = []
        
        for form_num in range(1, self.num_forms + 1):
            print(f"\nPreparing to scan form {form_num} of {self.num_forms}")
            
            if self.use_duplex:
                # In duplex mode, we scan both sides at once
                input("Place the form in the scanner and press Enter to scan both sides...")
                
                try:
                    print("Scanning...")
                    self.scanner.start()
                    image = self.scanner.snap()
                    
                    # Save front side
                    filename_front = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_front.png"
                    image.save(filename_front)
                    scanned_files.append(filename_front)
                    print(f"Front saved to: {filename_front}")
                    
                    # For duplex scanning, we should get a second image automatically
                    try:
                        image_back = self.scanner.snap()
                        filename_back = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_back.png"
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
                    filename_front = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_front.png"
                    image.save(filename_front)
                    scanned_files.append(filename_front)
                    print(f"Front saved to: {filename_front}")
                except Exception as e:
                    print(f"Error scanning front: {e}")
                    continue
                
                input("Place the BACK of the form in the scanner and press Enter...")
                
                try:
                    print("Scanning back...")
                    self.scanner.start()
                    image = self.scanner.snap()
                    filename_back = f"./Scans/{self.today}_Form{self.form_type}-{self.wid}_form{form_num}_back.png"
                    image.save(filename_back)
                    scanned_files.append(filename_back)
                    print(f"Back saved to: {filename_back}")
                except Exception as e:
                    print(f"Error scanning back: {e}")
        
        self.scanner.close()
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
        
        front_overlay = Image.open(front_overlay_path)
        back_overlay = Image.open(back_overlay_path)
        
        for i, scan_path in enumerate(scanned_files):
            try:
                scan = Image.open(scan_path)
                
                # Determine if this is a front or back page
                is_front = "_front.png" in scan_path
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
