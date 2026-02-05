import pdfplumber
import re
import json
import sys
import os

# Target the JS file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "new_data.js")

def extract_marks_from_pdf(pdf_path):
    marks_map = {}
    print(f"Reading ETC T4 Compiled Marksheet: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        count_ab = 0
        total_extracted = 0
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # ETC T4 Compiled Format (same as FCSP T4):
                    # Index 4: Enrollment (e.g., 24002171310074)
                    # Index 8: Marks (e.g., 48.0)
                    if not row or len(row) < 9: 
                        continue
                    
                    enrollment = str(row[4]).strip()
                    mark_str = str(row[8]).strip()
                    
                    # Validate Enrollment format
                    if not enrollment.isdigit() or len(enrollment) < 10:
                        continue
                        
                    mark_str_clean = mark_str.replace('\n', ' ').strip().upper()
                    
                    if mark_str_clean in ['AB', 'NONE', '']:
                        mark = 0.0
                        if mark_str_clean == 'AB': count_ab += 1
                    else:
                        try:
                            mark = float(mark_str_clean.replace(' ', ''))
                        except ValueError:
                            match = re.search(r'[\d\.]+', mark_str_clean)
                            if match:
                                mark = float(match.group(0))
                            else:
                                mark = 0.0
                    
                    marks_map[enrollment] = mark
                    total_extracted += 1
    
    print(f"Extracted marks for {total_extracted} entries.")
    if count_ab > 0:
        print(f"Found {count_ab} students marked 'AB' (Absent).")
    return marks_map

def update_js_data(target_subject, marks_map):
    print(f"Updating data in: {DATA_FILE_PATH}")
    print(f"Target Subject Field: '{target_subject}'")
    
    if not os.path.exists(DATA_FILE_PATH):
        print(f"Error: {DATA_FILE_PATH} not found.")
        return

    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the data array
    match = re.search(r'const data = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const data' array in new_data.js.")
        return
    
    data_str = match.group(1)
    
    # Convert JS object literals to JSON
    json_str = data_str
    json_str = re.sub(r'(\w+):', r'"\1":', json_str)
    json_str = re.sub(r',\s*\}', '}', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        return

    updated_count = 0
    for student in data:
        enrollment = str(student.get('enrollment', ''))
        
        if enrollment in marks_map:
            # Updating the etc field
            student[target_subject] = marks_map[enrollment]
            updated_count += 1
                
    print(f"Updated records for {updated_count} students in new_data.js.")

    # Reconstruct the JS file
    new_data_lines = ["const data = ["]
    for i, item in enumerate(data):
        line_json = json.dumps(item)
        line_js = re.sub(r'"(\w+)":', r'\1:', line_json)
        line = "  " + line_js
        if i < len(data) - 1: line += ","
        new_data_lines.append(line)
    new_data_lines.append("];")
    
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write("\n".join(new_data_lines))
    print("new_data.js updated successfully.")

def main():
    print("--- ETC T4 Compiled Marks Updater ---")
    
    if len(sys.argv) < 2:
        print("Usage: python update_etc_t4_compiled.py <pdf_file>")
        print("Example: python update_etc_t4_compiled.py my_etc_marks.pdf")
        return

    pdf_input = sys.argv[1]
    target_subject = "etc"

    if not os.path.isabs(pdf_input):
        pdf_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), pdf_input)
    
    marks = extract_marks_from_pdf(pdf_input)
    if marks:
        update_js_data(target_subject, marks)

if __name__ == "__main__":
    main()
