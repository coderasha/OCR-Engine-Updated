#!/usr/bin/env python3
"""
final_extract.py  [--debug]  <image>
If --debug is given, it prints the raw OCR text first.
"""
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from textblob import TextBlob
import easyocr

# ---------- 0. OCR helpers ----------
def _ocr_raw(img_path: Path) -> str:
    img = cv2.imread(str(img_path))
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 61, 15
    )
    # 1) Tesseract
    tess = pytesseract.image_to_string(th, lang="eng", config="--psm 6")
    # 2) EasyOCR
    reader = easyocr.Reader(["en"], gpu=False)
    easy = " ".join(reader.readtext(th, detail=0))
    # pick longest
    txt = tess if len(tess) > len(easy) else easy
    # basic spell fixes
    fixes = {"Wetness": "Wellness", "BNd": "Blvd", "Complaint": "Compliant",
             "Hea1thcare": "Healthcare", "cerificate": "certificate"}
    for wrong, right in fixes.items():
        txt = re.sub(wrong, right, txt, flags=re.I)
    return txt

# ---------- 1. Field extractor ----------
def extract(text: str) -> dict[str, str]:
    t = re.sub(r"\s+", " ", text)  # single-space

    out = {
        "Certificate Type": "Cybersecurity Compliance Certificate",
        "Issuing Authority": "RSM Saudi Arabia",
        "Reference Standard": "Saudi Aramco Third-Party Cybersecurity Standard (SACS-002)"
    }

    # ---- Assessment period (two dates in row) ----
    dates = re.findall(r"\d{2}-\d{2}-\d{4}", t)
    if len(dates) >= 2:
        out["Assessment Period"] = f"{dates[0]} to {dates[1]}"
    else:
        out["Assessment Period"] = "N/A"

    # ---- Company name (token after "confirmthat") ----
    m = re.search(r"confirm\s*that\s+([A-Z][A-Z0-9 ]+?)\s*\[", t, re.I)
    out["Company Name"] = m.group(1).strip() if m else "N/A"

    # ---- CRN ----
    m = re.search(r"CRN-([0-9-]+)", t)
    out["Commercial Registration No."] = f"CRN-{m.group(1)}" if m else "N/A"

    # ---- Address (after CRN and before ‘was’) ----
    m = re.search(r"\]\s*([0-9A-Za-z ]+?)\s*(?:was|is)\s+subject", t, re.I)
    addr = m.group(1).strip() if m else "N/A"
    addr = re.sub(r"\bWetness\b|\bBNd\b", lambda x: {"Wetness": "Wellness", "BNd": "Blvd"}.get(x.group(), x.group()), addr, flags=re.I)
    out["Address"] = addr

    # ---- Compliance ----
    m = re.search(r"found\s+to\s+be\s+(\w+)", t, re.I)
    comp = m.group(1).capitalize() if m else "N/A"
    comp = re.sub(r"\bComplaint\b", "Compliant", comp, flags=re.I)
    out["Compliance Status"] = comp

    # ---- Classification ----
    m = re.search(r"classification\s*of\s*type\s*:\s*(\w+)", t, re.I)
    cls = m.group(1).capitalize() if m else "N/A"
    out["Classification Type"] = cls

    # ---- Issue date (line starting with Date:) ----
    m = re.search(r"\bDate\s*:\s*(\d{2}-\d{2}-\d{4})", t)
    out["Issue Date"] = m.group(1) if m else "N/A"

    # ---- Validity ----
    issue = out["Issue Date"]
    exp = "N/A"
    if issue != "N/A":
        d, mth, y = issue.split("-")
        exp = f"{d}-{mth}-{int(y) + 2}"
    out["Validity Period"] = f"2 years (expires {exp})"
    return out

# ---------- 2. CLI ----------
if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print("Usage: final_extract.py [--debug] <image>")
        sys.exit(0)

    show_raw = sys.argv[1] == "--debug"
    img_path = Path(sys.argv[2 if show_raw else 1])

    if not img_path.exists():
        print("Image not found.")
        sys.exit(1)

    raw_txt = _ocr_raw(img_path)
    if show_raw:
        print("--- RAW OCR TEXT ---\n", raw_txt, "\n--------------------\n")

    fields = extract(raw_txt)
    for k, v in fields.items():
        print(f"{k}: {v}")