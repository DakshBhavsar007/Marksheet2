import pdfplumber
import re
import json
import argparse
import sys
import os

# Target the JS file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "new_data.js")

SUBJECT_MAP = {
    "ps": "ps",
    "fsd": "fsd",
    "de": "de",
    "python": "fcsp", 
    "fcsp": "fcsp",
    "etc": "etc"
}

def extract_marks_from_pdf(pdf_path):
    marks_map = {}
    print(f"Reading Compiled PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        count_ab = 0
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Compiled Marksheet Format: At least 9 columns
                    # Name is at index 6
                    # Marks is at index 8
                    
                    if not row or len(row) < 9: continue
                    
                    name = str(row[6]).strip().upper()
                    mark_str = str(row[8]).strip()
                    
                    # Basic validation: Name should be reasonable length
                    if len(name) < 3 or name == "NAME" or name == "SUBJECT NAME": 
                        continue
                        
                    mark_str_clean = mark_str.replace('\n', ' ').strip().upper()
                    
                    if mark_str_clean == 'AB' or mark_str_clean == 'NONE':
                        mark = 0.0
                        if mark_str_clean == 'AB': count_ab += 1
                    else:
                        try:
                            clean_num = mark_str.replace(' ', '')
                            mark = float(clean_num)
                        except ValueError:
                            match = re.search(r'[\d\.]+', mark_str)
                            if match:
                                mark = float(match.group(0))
                            else:
                                continue # Skip header or invalid rows
                    
                    marks_map[name] = mark
    
    print(f"Extracted marks for {len(marks_map)} students.")
    print(f"Found {count_ab} students marked 'AB' (Absent).")
    return marks_map

def update_js_data(target_subject, marks_map):
    print(f"Updating Data file: {DATA_FILE_PATH}")
    print(f"Target Subject Key: '{target_subject}'")
    
    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'const data = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const data' array in new_data.js.")
        return
    
    data_str = match.group(1)
    
    # 1. Add quotes to keys {roll: -> {"roll":
    json_str = data_str
    json_str = re.sub(r'(\w+):', r'"\1":', json_str)
    
    # Trailing commas are invalid in JSON, remove them
    json_str = re.sub(r',\s*\}', '}', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error during preparation: {e}")
        return

    updated_count = 0
    
    for student in data:
        # Match by Name
        name = str(student.get('name', '')).strip().upper()
        
        # Ensure target key exists
        if target_subject not in student:
            student[target_subject] = 0.0

        if name in marks_map:
            pdf_mark = marks_map[name]
            
            # Logic: New = Old + PDF (No division by 2)
            old_val = float(student.get(target_subject, 0))
            new_val = old_val + pdf_mark
            
            student[target_subject] = new_val
            updated_count += 1
    
    print(f"Updated records for {updated_count} students.")

    new_data_lines = ["const data = ["]
    for i, item in enumerate(data):
        line_json = json.dumps(item)
        # Remove quotes around keys
        line_js = re.sub(r'"(\w+)":', r'\1:', line_json)
        
        line = "  " + line_js
        if i < len(data) - 1: line += ","
        new_data_lines.append(line)
    new_data_lines.append("];")
    
    new_content = "\n".join(new_data_lines)
    
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("new_data.js updated successfully.")

def main():
    print("--- Marks Updater (Compiled Marksheet - No Division) ---")
    
    if len(sys.argv) < 3:
        print("Usage: python update_marks_compiled_nodiv.py <pdf_file> <subject>")
        return

    pdf_input = sys.argv[1]
    subject_input = sys.argv[2].lower()

    if subject_input not in SUBJECT_MAP:
        print(f"Invalid subject '{subject_input}'. Valid options: {list(SUBJECT_MAP.keys())}")
        return

    internal_key = SUBJECT_MAP[subject_input]
    
    if not os.path.isabs(pdf_input):
        pdf_input = os.path.join(os.path.dirname(DATA_FILE_PATH), pdf_input)
    
    marks = extract_marks_from_pdf(pdf_input)
    if marks:
        update_js_data(internal_key, marks)

if __name__ == "__main__":
    main()
