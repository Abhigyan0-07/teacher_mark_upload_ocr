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
    # 1. Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 2. Upscale for better contour detection
    scale = 2.0
    width = int(gray.shape[1] * scale)
    height = int(gray.shape[0] * scale)
    dim = (width, height)
    resized = cv2.resize(gray, dim, interpolation=cv2.INTER_CUBIC)

    # 3. Threshold (Otsu) - Invert first to find white text on black background for contours
    # But usually paper is white, text is black. 
    # Thresholding: 
    #   cv2.THRESH_BINARY_INV: Text becomes White, Background Black (Best for finding contours of text)
    _, th_inv = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 4. Find Contours
    contours, _ = cv2.findContours(th_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 5. Filter Candidates
    # If no contours found, it's empty
    if not contours:
        return 0

    # Find largest contour by area (assuming it's the digit)
    # Filter out very small noise
    valid_contours = [c for c in contours if cv2.contourArea(c) > 50]
    
    if not valid_contours:
        return 0
        
    largest_c = max(valid_contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_c)
    
    # 6. Extract Digit and Center it
    # ROI of the digit from the INVERTED text (White text, Black BG) or Original?
    # Tesseract likes Black text on White background.
    # So let's extract from the 'resized' (original gray scaled) but we need to threshold it 
    # to be clean black/white first.
    
    # Let's get a clean black-text-white-bg version of the whole image first
    _, th_clean = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    digit_roi = th_clean[y:y+h, x:x+w]
    
    # Create a square canvas to center the digit
    # Size should be max(w, h) + padding
    side = max(w, h) + 40 # 20px padding each side
    canvas = np.ones((side, side), dtype=np.uint8) * 255 # White canvas
    
    # Center coordinates
    c_x = side // 2
    c_y = side // 2
    
    # Top-left dict
    dx = c_x - w // 2
    dy = c_y - h // 2
    
    # Paste digit
    canvas[dy:dy+h, dx:dx+w] = digit_roi
    
    # Save debug image
    import os
    import time
    debug_dir = r"C:\Users\abhig\OneDrive\Desktop\marks\backend\debug_crops"
    os.makedirs(debug_dir, exist_ok=True)
    timestamp = int(time.time() * 1000)
    # Use extensive filename to avoid collisions and know order
    is_saved = cv2.imwrite(f"{debug_dir}/{timestamp}_debug.png", canvas)
    print(f"[DEBUG] Saved crop to {debug_dir}/{timestamp}_debug.png: {is_saved}")

    # 7. Final OCR
    # PSM 10 is single char
    config = "--psm 10 -c tessedit_char_whitelist=0123456789"
    
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
        text = pytesseract.image_to_string(canvas, config=config)
        # print(f"[DEBUG] Raw OCR text: '{text.strip()}'")
    except pytesseract.TesseractNotFoundError:
        print("[ERROR] Tesseract not found.")
        raise Exception("Tesseract OCR is not installed on the server. Please install it.")
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return 0
        
    digits = "".join(ch for ch in text if ch.isdigit())
    val = int(digits) if digits else 0
    # print(f"[DEBUG] Parsed value: {val}")
    return val


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

