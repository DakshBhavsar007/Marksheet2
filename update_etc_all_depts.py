import pdfplumber
import re
import json
import os

# Target the JS file for all departments marksheet
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "new_datamarksheet.js")
PDF_PATH = os.path.join(os.path.dirname(__file__), "Compile_Marksheet_SEM_III_ETC.pdf")

def extract_marks_from_pdf(pdf_path):
    """Extract ETC marks from the compiled marksheet PDF"""
    marks_map = {}
    print(f"Reading ETC Compiled Marksheet: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        count_ab = 0
        total_extracted = 0
        for page_num, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # ETC Compiled Format:
                    # Index 4: Enrollment (e.g., 24002171310074)
                    # Index 8: Marks (e.g., 48.0)
                    if not row or len(row) < 9: 
                        continue
                    
                    enrollment = str(row[4]).strip() if row[4] else ""
                    mark_str = str(row[8]).strip() if row[8] else ""
                    
                    # Validate Enrollment format (should be numeric and at least 10 chars)
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
    
    print(f"Extracted marks for {len(marks_map)} unique enrollments.")
    if count_ab > 0:
        print(f"Found {count_ab} students marked 'AB' (Absent).")
    return marks_map

def update_js_data(marks_map):
    """Update the new_datamarksheet.js with ETC marks"""
    print(f"Updating data in: {DATA_FILE_PATH}")
    
    if not os.path.exists(DATA_FILE_PATH):
        print(f"Error: {DATA_FILE_PATH} not found.")
        return

    with open(DATA_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract the data array
    match = re.search(r'const data = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const data' array in new_datamarksheet.js.")
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
    not_found = []
    
    for student in data:
        enrollment = str(student.get('enrollment', ''))
        
        if enrollment in marks_map:
            # Adding/updating the 'etc' field
            student['etc'] = marks_map[enrollment]
            updated_count += 1
        else:
            # If not found in PDF, set etc to 0 (or keep existing if any)
            if 'etc' not in student:
                student['etc'] = 0.0
            not_found.append(enrollment)
                
    print(f"Updated ETC marks for {updated_count} students.")
    print(f"Students not found in PDF: {len(not_found)}")
    if not_found and len(not_found) <= 20:
        print(f"Not found enrollments: {not_found[:20]}")

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
    print("new_datamarksheet.js updated successfully with ETC marks!")

def main():
    print("=" * 50)
    print("ETC Marks Updater for All Departments")
    print("=" * 50)
    
    marks = extract_marks_from_pdf(PDF_PATH)
    if marks:
        update_js_data(marks)
    else:
        print("No marks extracted. Please check the PDF file.")

if __name__ == "__main__":
    main()
