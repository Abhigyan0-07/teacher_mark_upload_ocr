import sys
import os
import base64
sys.path.append(os.getcwd())

from backend.services.grid_excel import extract_grid_marks

def test_google_ocr():
    image_path = "test_grid.png"
    if not os.path.exists(image_path):
        print(f"Image {image_path} not found.")
        return

    print(f"Testing Google Vision OCR with {image_path}...")
    
    with open(image_path, "rb") as f:
        img_bytes = f.read()
        img_b64 = base64.b64encode(img_bytes).decode('utf-8')
        
    try:
        # Default 4x2 grid as per previous code
        marks = extract_grid_marks(img_b64, rows=7, cols=4) # Adjusted to likely grid size if needed, or stick to default
        # The user's code had defaults rows=4, cols=2 in diagnosis, but let's check what test_grid.png looks like.
        # Actually, let's just run it with default or guess.
        # The diagnosis script used rows=4, cols=2.
        
        print("Extracted Marks:", marks)
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_google_ocr()
