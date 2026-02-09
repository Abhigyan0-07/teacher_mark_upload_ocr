# Mark Scanner & Auto-Grader

A web application for scanning physical marks sheets using a webcam, performing OCR to extract handwritten marks, and auto-populating an Excel sheet.

## Prerequisites

1.  **Python 3.10+**: For the backend API.
2.  **Node.js 16+**: For the frontend React app.
3.  **Tesseract OCR**: Required for reading text from images.
    *   **Windows**: Download and install from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
    *   Ensure the installation path (e.g., `C:\Program Files\Tesseract-OCR`) is added to your system PATH, or the app will attempt to auto-detect it.

## Installation

### 1. Backend (FastAPI)

```bash
# Navigate to the root folder
cd marks

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate
# Mac/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend (React + Vite)

```bash
# Navigate to the frontend folder
cd frontend

# Install dependencies
npm install
```

## Running the Application

You need to run the **Backend** and **Frontend** in two separate terminals.

### Terminal 1: Backend

```bash
# Make sure you are in the root 'marks' folder and venv is active
.venv\Scripts\Activate

# Start the server
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
*   The API will be available at `http://localhost:8000`.
*   Swagger verification docs: `http://localhost:8000/docs`.

### Terminal 2: Frontend

```bash
# Navigate to the frontend folder
cd frontend

# Start the development server
npm run dev
```
*   The UI will be available at `http://localhost:5173`.

## Usage

1.  Open the frontend in your browser.
2.  Log in as a Teacher.
3.  Navigate to the **Scanner** page.
4.  Configure the grid dimensions (Rows x Columns) to match your physical sheet.
5.  Align the sheet in the camera view and click **Scan**.
6.  Marks will be extracted and can be downloaded as an Excel file.
