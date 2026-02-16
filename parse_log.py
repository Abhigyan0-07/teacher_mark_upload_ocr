
# Script to read backend_debug.log and print the last relevant lines
import os

LOG_FILE = r"C:\Users\abhig\OneDrive\Desktop\marks\backend_debug.log"

if not os.path.exists(LOG_FILE):
    print("Log file not found.")
    exit()

with open(LOG_FILE, "r") as f:
    lines = f.readlines()

# Get last 2000 lines
recent_lines = lines[-2000:]

# Filter for our debug tags
debug_lines = [line.strip() for line in recent_lines if "[Fallback-Debug]" in line or "Mismatch" in line or "Processing image" in line]

with open("parsed_logs.txt", "w") as out:
    out.write(f"--- Found {len(debug_lines)} relevant log lines ---\n")
    for line in debug_lines:
        out.write(line + "\n")
print("Logs written to parsed_logs.txt")
