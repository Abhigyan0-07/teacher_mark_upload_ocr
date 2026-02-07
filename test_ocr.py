import cv2
import numpy as np
import base64
import requests
import json

def create_test_image():
    # Create a white image (simulation of paper)
    # 4 rows, 2 columns. Let's make it typical webcam resolution cropped say 800x600 for the grid
    h, w = 600, 800
    img = np.ones((h, w, 3), dtype=np.uint8) * 255
    
    # Draw grid lines (optional, but good for visual)
    # The backend splits purely by geometry: row_height = h//4, col_width = w//2
    row_h = h // 4
    col_w = w // 2
    
    # Values we want to write
    # Row 0: 15, 08
    # Row 1: 20, 10
    # Row 2: 05, 12
    # Row 3: 00, 09
    values = [
        [15, 8],
        [20, 10],
        [5, 12],
        [0, 9]
    ]
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    for r in range(4):
        for c in range(2):
            val = values[r][c]
            text = f"{val:02d}"
            
            # Center of the cell
            cx = c * col_w + col_w // 2
            cy = r * row_h + row_h // 2
            
            # Write text roughly in center
            # Using Hershey Simplex to look somewhat like printed/handwritten text
            cv2.putText(img, text, (cx - 40, cy + 20), font, 2, (0, 0, 0), 3, cv2.LINE_AA)
            
            # Draw box border for visualization (backend doesn't need lines, it cuts strictly)
            cv2.rectangle(img, (c*col_w, r*row_h), ((c+1)*col_w, (r+1)*row_h), (0,0,0), 2)
            
    # Save for manual inspection
    cv2.imwrite("test_grid.png", img)
    
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

    b64_img = create_test_image()
    print("Test image created: test_grid.png")
    
    url = "http://localhost:8000/api/teacher/scan-grid-excel"
    payload = {
        "image_base64": b64_img,
        # "excel_file": None 
    }
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print("Sending request to backend...")
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            data = res.json()
            print("\nSUCCESS!")
            print(f"Marks: {data['marks']}")
            print(f"Total: {data['total']}")
            
            expected = [15, 8, 20, 10, 5, 12, 0, 9]
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
