
# Script to check indentation around potential error lines
with open(r"c:\Users\abhig\OneDrive\Desktop\marks\backend\services\grid_excel.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []

def check_line(i):
    if 0 <= i < len(lines):
        output.append(f"Line {i+1}: {repr(lines[i])}")

# Check lines around 303 (extract_grid_marks loop)
output.append("--- Around Line 303 ---")
for i in range(298, 308):
    check_line(i)

# Check lines around 622 (fallback loop)
output.append("\n--- Around Line 622 ---")
for i in range(618, 628):
    check_line(i)

# Check lines around 318 (smart_grid_cluster definition)
output.append("\n--- Around Line 318 ---")
for i in range(315, 321):
    check_line(i)

with open("check_indent_out.txt", "w") as f:
    f.write("\n".join(output))
