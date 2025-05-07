# Prompt for Python Script

Used Claude: Anthropic 3.7 Sonnet

## Prompt:
```
We have been building the python Scan-to-Redact-to-OCR python script.

I need to refactor this for my work flow. The code and readme are attached.

First issue: I have a "hanging connection" bug that needs to be fixed  (i.e., the python script terminates when the forms are done scanning -- BUT the fujitsu scanner shows a wheel thinking/spinning/processing icon on the LCD) . Once the python script terminates it should safely close the connection (I have to pull the USB to force the scanner to reset/close the job).

Second issue: "Steps" are all greatly documented for the stdout/print(), but there should be clear spacing (e.g., an empty line break) or section dividers (e.g., a bunch of dashses) that make it more easily readable.

Third issue: the OCR capability (Phase 3) is NOT always wanted -- the script should ask on start if the user wants OCR (default yes, enter == yes; [Y/n]). And skip the step.

Last issue: the workflow is wrong, after gaining feedback from my users/stakeholders. What is desired: (a) the scanner is found/initialized, (b) the user is asked if OCR is wanted, then (c) the "scanning loop" starts -- this will then (i) ask for the 10 digit ID (OR -- if already entered the user can simply press "enter" to re-use the number), (ii) ask for the Form 2 or 3 type (i.e., only 2 or 3 is the acceptable answer), (iii) the "two + one phases"  (i.e., the original 3 phase may have OCR skipped) start -- the file is scanned, then merge/redacted, and (iv) the "would you like to scan another form?" Loop question is asked (i.e., [Y/n]] is provided -- enter means continue -- n+enter will close the script and safely close connection to the scanner).

Ask all relevant questions before starting. 
```

NOTE -- no questions were asked.

## Missed issue:
-- form naming convention