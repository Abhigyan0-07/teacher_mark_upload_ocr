import base64
import io
from pathlib import Path
from typing import List

import cv2
import numpy as np
import pytesseract
from PIL import Image
from openpyxl import Workbook, load_workbook
from fastapi import HTTPException


def _decode_base64_image(image_b64: str) -> np.ndarray:
    header, _, data = image_b64.partition(",")
    if data:
        image_b64 = data
    img_bytes = base64.b64decode(image_b64)
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    open_cv_image = np.array(img)
    open_cv_image = open_cv_image[:, :, ::-1].copy()  # RGB -> BGR
    return open_cv_image


def _ocr_box(image: np.ndarray) -> int:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    th = cv2.resize(th, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    config = "--psm 6 -c tessedit_char_whitelist=0123456789"
    
    # Auto-detect tesseract if likely missing
    import shutil
    import os
    if not shutil.which("tesseract"):
        possible_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                pytesseract.pytesseract.tesseract_cmd = p
                break

    try:
        text = pytesseract.image_to_string(th, config=config)
    except pytesseract.TesseractNotFoundError:
        # Fallback or re-raise with clear message
        # Since this is deep in service, we might just log or return 0, 
        # but for the user to know, we should probably raise a specific exception 
        # that the route handler can catch.
        raise Exception("Tesseract OCR is not installed on the server. Please install it.")
    except Exception:
        return 0
        
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def extract_grid_marks(image_b64: str, rows: int = 4, cols: int = 2) -> List[int]:
    """
    Extract marks from a fixed grid of (rows x cols) boxes covering the ROI.
    Boxes are read row-wise: top-left to bottom-right.
    """
    image = _decode_base64_image(image_b64)
    h, w = image.shape[:2]

    marks: List[int] = []
    row_height = h // rows
    col_width = w // cols

    for r in range(rows):
        for c in range(cols):
            y1 = r * row_height
            y2 = (r + 1) * row_height if r < rows - 1 else h
            x1 = c * col_width
            x2 = (c + 1) * col_width if c < cols - 1 else w
            box = image[y1:y2, x1:x2]
            marks.append(_ocr_box(box))

    return marks


def append_marks_to_excel(
    marks: List[int],
    excel_content: bytes | None = None
) -> tuple[int, bytes]:
    """
    Append a row with marks and total to an Excel sheet.
    If excel_content is None, creates a new workbook.
    Returns (total, modified_excel_bytes).
    """
    total = sum(marks)

    if excel_content:
        # Load from bytes
        wb = load_workbook(io.BytesIO(excel_content))
        ws = wb.active
    else:
        # Create new
        wb = Workbook()
        ws = wb.active
        # Header row
        for idx in range(len(marks)):
            ws.cell(row=1, column=idx + 1).value = f"Q{idx + 1}"
        ws.cell(row=1, column=len(marks) + 1).value = "Total"

    row = ws.max_row + 1
    for idx, value in enumerate(marks):
        ws.cell(row=row, column=idx + 1).value = value
    ws.cell(row=row, column=len(marks) + 1).value = total

    # Save to bytes
    out_buffer = io.BytesIO()
    wb.save(out_buffer)
    out_buffer.seek(0)
    return total, out_buffer.getvalue()

