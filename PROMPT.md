# Prompt for Python Script

Used Claude: Anthropic 3.7 Sonnet

## Prompt:
```
I have Privacy Act Data in assessment forms, which are paper-based that I want to digitize. I have ubuntu linux 24.04, which has access to a (up to a duplex) scanner. There are two main forms -- Form 2 and Form 3. Each have a front and back, which I have "overlay images" (i.e., mostly transparent 8.5" x 11" .pngs -- but have black redaction areas filled out that blocks the privacy act areas).

I need a python based Scan-to-Redact-to-OCR solution script. Note: I do NOT need "just pdfs" -- PNGs are equivalent for "visual inspection".

Phase 0: ask user for "WID" (i.e., 10 digit, UUID-like student number) and "Form Type" (i.e., either 2, or 3) -- which can be "input based" (i.e., the class press 1 or 2 -- that the program then computes/moves to next stage)

Phase I: access the USB scanner to collect all documents. Save to ./Scans/YYYY-MM-DD_Form#-WID.(file) (i.e., ISO/current date for the prefix, Form# based on input; for 'file' -- it COULD be a pdf -- BUT if it's easier to save the usb-scan data to a png -- then merge it in Phase II -- then skip making a PDF for now!)

Phase II: based on the Form Type ... look into ./redaction-overlays/* for Form-#-front.png or Form-#-back.png (i.e., # is either 2 or 3 -- and the front is for odd page scans, and the even is the back)... then merge INTO ./Redactions/REDACTED_<file name in Phase I>. This protects student privacy!

This is the MVP/threshold goal!

Phase III: For the strectch/objective goal, I want to try to OCR the data into a text. Ideally this would be a PDF that a user can use a mouse to click/drag/highlight.

Ask all relevant questions before starting.
```

## Response Questions from Claude:
```
I understand you need a Python script to help digitize paper-based assessment forms while protecting privacy data. Let me ask a few clarifying questions before I start creating the solution:

1. Do you already have the redaction overlays created (Form-2-front.png, Form-2-back.png, Form-3-front.png, Form-3-back.png), or will these need to be created as part of the solution?
2. For scanning, do you have a specific scanning library/tool already installed (like SANE, pyinsane2, etc.) that you prefer to use?
3. When merging the scans with redaction overlays, what's your preference for handling the alignment? Should the overlay be precisely aligned with specific coordinates, or should it just cover the entire page?
4. For the OCR component (Phase III), do you have a preference for the OCR engine? (Tesseract is a common choice)
5. For the final output in Phase III, would you prefer a searchable PDF or is plain text output sufficient?

Once I have this information, I'll create a comprehensive solution that handles all three phases of your requirements.
```

## My Response to Claude on Questions:
```
1. (sic; meant 0) I failed to mention the "ask the user" for double sided vs. single side -- OR have the script determine if "duplex scanning" is possible! (i.e., they might want to scan front/back -- but the script should alert the user!)

1. I already made this to scale, 8.5" x 11" on GIMP.
2. I do NOT have a library installed -- I'd use the most common/capable one to ensure longest support (or easiet trouble shooting) for the script.
3. The scanner "Should" scan in Letter-sized (8.5" by 11") documents -- thus the scanned files, and overlays are predictable. Note -- on #0 -- the human will insert blank pages in the event of single page scanning (i.e., duplex might have a "blank back" -- but will always scan evenly -- in the event of a single-sided scanning -- the user will manually correct missing pages).
4. No preference -- see #2 -- Tesseract sounds fine!
5. Plain text would be the minimal product (place also in the same formatting/naming convention -- but make it TEXT) -- the ideal (for the general admin/staff user) is PDF-based products.
```

## Final response pre-generation:
```
Thank you for the clarifications! I'll create a Python script that addresses all your requirements. The script will:

1. Check if duplex scanning is available and alert the user accordingly
2. Ask for WID and Form Type
3. Scan documents using SANE (a common and well-supported scanning library)
4. Apply redaction overlays to protect privacy data
5. Generate OCR'd text using Tesseract
6. Create both plain text files and searchable PDFs

Let me create this solution for you:
```
