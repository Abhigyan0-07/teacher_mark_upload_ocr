import base64
import io
import re
from typing import List

import cv2
import numpy as np
import pytesseract
from PIL import Image

from ..schemas.core import MarkItem


QUESTION_MARK_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<label>               # question label group
        (?:Q\s*)?            # optional leading Q
        \d+                  # main number
        (?:[a-zA-Z]|\([a-zA-Z]\))?   # optional subpart like a or (b)
    )
    [\s:-]+
    (?P<marks>\d+)
    \s*$
    """,
    re.VERBOSE,
)


def _decode_base64_image(image_b64: str) -> np.ndarray:
    header, _, data = image_b64.partition(",")
    if data:
        image_b64 = data
    img_bytes = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    open_cv_image = np.array(img)
    open_cv_image = open_cv_image[:, :, ::-1].copy()  # RGB to BGR
    return open_cv_image


def _preprocess_image(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2,
    )
    scaled = cv2.resize(thresh, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    return scaled


def _setup_tesseract_path():
    """
    Attempt to find Tesseract executable in common locations if not in PATH.
    """
    import os
    import shutil

    # If already in path, good
    if shutil.which("tesseract"):
        return

    # Common Windows paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
    ]

    for p in possible_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            print(f"Found Tesseract at {p}")
            return


def run_ocr_on_base64_image(image_b64: str) -> List[MarkItem]:
    _setup_tesseract_path()
    image = _decode_base64_image(image_b64)
    preprocessed = _preprocess_image(image)

    config = "--psm 6 -c tessedit_char_whitelist=0123456789Qq()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ:- "
    raw_text = pytesseract.image_to_string(preprocessed, config=config)

    entries: List[MarkItem] = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = QUESTION_MARK_PATTERN.match(line)
        if not match:
            continue
        label = match.group("label")
        marks = int(match.group("marks"))
        label = label.replace(" ", "").upper()
        entries.append(MarkItem(question_label=label, marks=marks))

    return entries

