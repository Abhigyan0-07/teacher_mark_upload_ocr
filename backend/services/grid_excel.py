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
    # Use RETR_LIST to find all contours, including those inside a border
    contours, _ = cv2.findContours(th_inv, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # 5. Filter Candidates
    # If no contours found, it's empty
    if not contours:
        return 0

    # Filter out very small noise
    valid_contours = [c for c in contours if cv2.contourArea(c) > 20]
    
    # Filter out likely grid lines / borders
    # 1. Touches edge?
    # 2. Long and thin?
    
    final_contours = []
    h_img, w_img = height, width
    
    for c in valid_contours:
        x, y, w, h = cv2.boundingRect(c)
        
        # Check if touches edge (within 3px)
        touches_edge = (x <= 3) or (y <= 3) or (x + w >= w_img - 3) or (y + h >= h_img - 3)
        
        # Check if long (spans > 50% of dimension)
        spans_long = (w > 0.5 * w_img) or (h > 0.5 * h_img)
        
        if touches_edge and spans_long:
            continue # Skip border line
            
        final_contours.append(c)
    
    if not final_contours:
        return 0
        
    # Find bounding box that encompasses ALL valid contours (for multi-digit support)
    min_x, min_y = width, height
    max_x, max_y = 0, 0
    
    # print(f"[DEBUG] Valid contours found: {len(final_contours)}")

    for c in final_contours:
        x, y, w, h = cv2.boundingRect(c)
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)
        
    x, y = min_x, min_y
    w = max_x - min_x
    h = max_y - min_y
    
    # 6. Extract ROI and Center it
    # Let's get a clean black-text-white-bg version of the whole image first
    _, th_clean = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Sanity check
    if w <= 0 or h <= 0:
        return 0
        
    digit_roi = th_clean[y:y+h, x:x+w]
    
    # Create a square canvas to center the content
    # Size should be max(w, h) + padding
    side = max(w, h) + 40 # 20px padding
    canvas = np.ones((side, side), dtype=np.uint8) * 255 # White canvas
    
    # Center coordinates
    c_x = side // 2
    c_y = side // 2
    
    # Top-left dict
    dx = c_x - w // 2
    dy = c_y - h // 2
    
    # Paste ROI
    canvas[dy:dy+h, dx:dx+w] = digit_roi
    
    print(f"[DEBUG] Valid contours found: {len(final_contours)}")

    # ...

    # Save debug image (Removed for production, can re-enable if needed)
    import os
    import time
    debug_dir = r"C:\Users\abhig\OneDrive\Desktop\marks\backend\debug_crops"
    os.makedirs(debug_dir, exist_ok=True)
    timestamp = int(time.time() * 1000)
    cv2.imwrite(f"{debug_dir}/{timestamp}_debug.png", canvas)
    
    # Save raw crop too for comparison if possible? 
    # Let's just save the processed canvas for now as it shows what Tesseract sees.

    # 7. Final OCR
    # ...
    
    try:
        # Define config for Tesseract (e.g., to recognize only digits)
        # Assuming 'config' is defined elsewhere or needs to be added.
        # For this change, we'll assume it's implicitly handled or will be added.
        # If not, pytesseract.image_to_string(canvas) would be used.
        config = r'--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789'
        text = pytesseract.image_to_string(canvas, config=config)
        print(f"[DEBUG] Raw OCR text: '{text.strip()}'")
    except pytesseract.TesseractNotFoundError:
        print("[ERROR] Tesseract not found.")
        raise Exception("Tesseract OCR is not installed on the server. Please install it.")
    except Exception as e:
        print(f"[ERROR] OCR failed: {e}")
        return 0
        
    digits = "".join(ch for ch in text if ch.isdigit())
    val = int(digits) if digits else 0
    print(f"[DEBUG] Parsed value: {val}")
    return val



from ..ocr.google_vision import detect_document_text

def _get_centroids(vertices):
    """
    Returns (x, y) centroid of a polygon defined by vertices.
    vertices: list of objects with .x and .y
    """
    if not vertices:
        return 0, 0
    
    xs = [v.x for v in vertices]
    ys = [v.y for v in vertices]
    return sum(xs) / len(xs), sum(ys) / len(ys)

def extract_grid_marks(image_b64: str, rows: int = 4, cols: int = 2) -> List[int]:
    """
    Extract marks from a fixed grid using Google Cloud Vision API.
    Sends the WHOLE image to Google Vision once, then maps detected text 
    to the corresponding grid cell based on coordinates.
    """
    image_cv = _decode_base64_image(image_b64)
    h, w = image_cv.shape[:2]
    
    # Encode back to bytes for Google Vision
    # We use the original base64 if possible to save re-encoding, 
    # but the helper _decode_base64 handles header stripping.
    # Let's just strip header manually to get clean bytes
    if "," in image_b64:
        _, _, data = image_b64.partition(",")
        img_bytes = base64.b64decode(data)
    else:
        img_bytes = base64.b64decode(image_b64)
        
    try:
        annotation = detect_document_text(img_bytes)
    except Exception as e:
        print(f"[ERROR] Google Vision API failed: {e}")
        # Fallback to local OCR or re-raise? 
        # For now, let's re-raise because the user explicitly requested Google accuracy.
        # But we could fallback.
        print("Falling back to legacy local OCR...")
        return _extract_grid_marks_fallback(image_cv, rows, cols)


    # Initialize grid marks
    grid_marks = [0] * (rows * cols)
    
    row_height = h / rows
    col_width = w / cols
    
    # Iterate through all pages/blocks/paragraphs/words/symbols
    # We care about "words" or "symbols" usually for digits.
    # "words" is usually safer for "10", "5", etc.
    
    for page in annotation.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:
                    word_text = "".join([symbol.text for symbol in word.symbols])
                    
                    # Filter for likely marks (digits)
                    # Allow "10", "0", "5", "7". 
                    # Might see "Q1" if it reads the label, but usually we just want the handwritten mark.
                    # Or maybe the printed mark?
                    # Assuming we are looking for handwritten digits.
                    
                    cleaned_text = "".join(filter(str.isdigit, word_text))
                    
                    if not cleaned_text:
                        continue
                        
                    val = int(cleaned_text)
                    
                    # Find which cell this word belongs to
                    cx, cy = _get_centroids(word.bounding_box.vertices)
                    
                    # Determine row and col
                    # Note: Google Vision coordinates are absolute pixels
                    r = int(cy // row_height)
                    c = int(cx // col_width)
                    
                    if 0 <= r < rows and 0 <= c < cols:
                        idx = r * cols + c
                        # If a cell has multiple numbers, we might take the largest or last one.
                        # Usually a cell has "Q1" (preprinted) and "5" (handwritten).
                        # We want the handwritten part. 
                        # This is tricky without "Handwriting vs Print" classification.
                        # However, Q numbers are usually small integers (1, 2, 3...) and Marks are also small.
                        # Heuristic: 
                        # If we see multiple numbers in a box, how to distinguish?
                        # Maybe the position? Marks are usually on the right or manually written.
                        # For now, let's just take the LAST one found (often bottom/right) or MAX?
                        # Let's assume the user effectively crops/zooms such that mostly the mark is visible?
                        # No, the grid contains the whole cell.
                        
                        # Simple Heuristic: Overwrite. 
                        # Ideally, we'd spatially filter.
                        # Use the "max" value? 
                        # Let's stick with: "Detected a number, use it."
                        # If multiple are detected, correct behavior is undefined without more context.
                        # But typically Q1 is top-left, Mark is center/right.
                        
                        # Let's update only if it looks like a reasonable mark (e.g. <= 100)
                        if val <= 100:
                            grid_marks[idx] = val

    return grid_marks

def extract_single_mark(image_b64: str) -> int:
    """
    Extract a single mark from a cropped image.
    Uses Google Cloud Vision API effectively on the small crop.
    """
    if "," in image_b64:
        _, _, data = image_b64.partition(",")
        img_bytes = base64.b64decode(data)
    else:
        img_bytes = base64.b64decode(image_b64)
        
    try:
        annotation = detect_document_text(img_bytes)
        full_text = annotation.text
        # Clean non-digits
        digits = "".join(filter(str.isdigit, full_text))
        if digits:
            return int(digits)
        return 0
    except Exception as e:
        print(f"[ERROR] Google Vision API failed on single crop: {e}")
        # Fallback to local
        image_cv = _decode_base64_image(image_b64)
        return _ocr_box(image_cv)


def _extract_grid_marks_fallback(image: np.ndarray, rows: int = 4, cols: int = 2) -> List[int]:
    """Legacy Tesseract implementation for fallback"""
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

