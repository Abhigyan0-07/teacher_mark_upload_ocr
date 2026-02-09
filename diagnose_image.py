import cv2
import numpy as np
import os

def diagnose():
    img_path = r"C:/Users/abhig/.gemini/antigravity/brain/3a2a1c6e-79b6-4b23-8043-97444490d490/uploaded_media_1770469531724.jpg"
    
    if not os.path.exists(img_path):
        print(f"Error: Image not found at {img_path}")
        # Try finding it in the current dir just in case
        return

    img = cv2.imread(img_path)
    if img is None:
        print("Error: Could not read image.")
        return

    h, w = img.shape[:2]
    
    # Defaults in backend
    rows = 4
    cols = 2
    
    row_height = h // rows
    col_width = w // cols
    
    print(f"Image Dimensions: {w}x{h}")
    print(f"Splitting into {rows} rows, {cols} cols")
    print(f"Cell Size: {col_width}x{row_height}")
    
    # Draw the grid that the backend sees
    viz = img.copy()
    
    # Draw horizontal lines
    for r in range(1, rows):
        y = r * row_height
        cv2.line(viz, (0, y), (w, y), (0, 0, 255), 3) # Red lines
        
    # Draw vertical lines
    for c in range(1, cols):
        x = c * col_width
        cv2.line(viz, (x, 0), (x, h), (0, 0, 255), 3) # Red lines
        
    out_path = "grid_diagnosis.jpg"
    cv2.imwrite(out_path, viz)
    print(f"Saved diagnosis visualization to {out_path}")

if __name__ == "__main__":
    diagnose()
