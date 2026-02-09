import cv2
import numpy as np
import base64
import requests
import json

def create_3x4_image():
    # Create a white image (simulation of paper)
    # 3 rows, 4 columns matrix to fit 0-9 and extras
    h, w = 600, 800
    img = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    rows = 3
    cols = 4
    
    row_h = h // rows
    col_width = w // cols
    
    # Values covering 0-9 and some double digits
    values = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 0, 10, 11]
    ]
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    for r in range(rows):
        for c in range(cols):
            val = values[r][c]
            text = f"{val}"
            
            # Center of the cell
            cx = c * col_width + col_width // 2
            cy = r * row_h + row_h // 2
            
            # Write text
            cv2.putText(img, text, (cx - 20, cy + 20), font, 2, (0, 0, 0), 3, cv2.LINE_AA)
            
            # Draw box border
            cv2.rectangle(img, (c*col_width, r*row_h), ((c+1)*col_width, (r+1)*row_h), (0,0,0), 2)
            
    # Save for manual inspection
    cv2.imwrite("test_3x4.png", img)
    
    # Encode to base64
    _, buffer = cv2.imencode('.png', img)
    return base64.b64encode(buffer).decode('utf-8')

def login():
    url = "http://localhost:8000/api/auth/login"
    data = {
        "username": "abhigyan",
        "password": "Abhigyan@001"
    }
    try:
        res = requests.post(url, data=data)
        if res.status_code == 200:
            return res.json()["access_token"]
        else:
            print(f"Login Failed: {res.text}")
            return None
    except Exception as e:
        print(f"Login Error: {e}")
        return None

def test_backend():
    token = login()
    if not token:
        print("Aborting test due to login failure.")
        return

    b64_img = create_3x4_image()
    print("Test image created: test_3x4.png")
    
    url = "http://localhost:8000/api/teacher/scan-grid-excel"
    payload = {
        "image_base64": b64_img,
        "rows": 3,
        "cols": 4
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print("Sending request to backend with rows=3, cols=4...")
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            data = res.json()
            print("\nSUCCESS!")
            print(f"Marks: {data['marks']}")
            print(f"Total: {data['total']}")
            
            expected = [1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 10, 11]
            if data['marks'] == expected:
                print("VERIFICATION PASSED: All marks match.")
            else:
                print(f"VERIFICATION FAILED: Expected {expected} but got {data['marks']}")
        else:
            print(f"FAILED. Status: {res.status_code}")
            print(res.text)
    except Exception as e:
        print(f"Error communicating with backend: {e}")

if __name__ == "__main__":
    test_backend()
