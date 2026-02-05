import pdfplumber
import re
import json
import sys
import os

# Target the JS file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "new_data.js")

def extract_marks_from_pdf(pdf_path):
    marks_map = {}
    print(f"Reading SY4 Marksheet: {pdf_path}")
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None

    with pdfplumber.open(pdf_path) as pdf:
        count_ab = 0
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Index 2: Enrollment (Reliable for SY4 PDFs)
                    # Index 7: Marks (Usually the last column or SEE column)
                    if not row or len(row) < 8: continue
                    
                    enrollment = str(row[2]).strip()
                    mark_str = str(row[7]).strip()
                    
                    # Basic validation: Enrollment should look like LJ's format (usually 14 digits)
                    if len(enrollment) < 10 or not enrollment.isdigit(): 
                        continue
                        
                    mark_str_clean = mark_str.replace('\n', ' ').strip().upper()
                    
                    if mark_str_clean == 'AB' or mark_str_clean == 'NONE' or mark_str_clean == '':
                        mark = 0.0
                        if mark_str_clean == 'AB': count_ab += 1
                    else:
                        try:
                            # Remove spaces and handle potential fractional marks
                            clean_num = mark_str_clean.replace(' ', '')
                            mark = float(clean_num)
                        except ValueError:
                            # Fallback using regex to find first number
                            match = re.search(r'[\d\.]+', mark_str_clean)
                            if match:
                                mark = float(match.group(0))
                            else:
                                mark = 0.0
                    
                    marks_map[enrollment] = mark
    
    print(f"Extracted marks for {len(marks_map)} students.")
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
    
    # Extract the data array from the JS file
    match = re.search(r'const data = (\[.*\]);', content, re.DOTALL)
    if not match:
        print("Error: Could not find 'const data' array in new_data.js.")
        return
    
    data_str = match.group(1)
    
    # Prepare for JSON parsing (JS object literals to JSON)
    json_str = data_str
    json_str = re.sub(r'(\w+):', r'"\1":', json_str)
    json_str = re.sub(r',\s*\}', '}', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error during preparation: {e}")
        return

    updated_count = 0
    skipped_count = 0
    
    for student in data:
        enrollment = str(student.get('enrollment', ''))
        
        # We only update if student enrollment is in our marks map
        if enrollment in marks_map:
            # Update/Set the mark (Directly as per user request: "marks is out of 100")
            student[target_subject] = marks_map[enrollment]
            updated_count += 1
        else:
            # If not in PDF, we might want to ensure the field exists to avoid undefined errors in JS
            if target_subject not in student:
                student[target_subject] = student.get(target_subject, 0.0)
            skipped_count += 1
    
    print(f"Updated records for {updated_count} students.")

    # Reconstruct the JS file to match original style
    new_data_lines = ["const data = ["]
    for i, item in enumerate(data):
        # Generate JSON representation
        line_json = json.dumps(item)
        # Convert to JS style (keys without quotes)
        line_js = re.sub(r'"(\w+)":', r'\1:', line_json)
        
        line = "  " + line_js
        if i < len(data) - 1: 
            line += ","
        new_data_lines.append(line)
    new_data_lines.append("];")
    
    new_content = "\n".join(new_data_lines)
    
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("new_data.js updated successfully.")

def main():
    print("--- SY4 OD/ETC Marks Updater (Out of 100) ---")
    
    if len(sys.argv) < 3:
        print("Usage: python update_marks_sy4_od_etc.py <pdf_file> <subject>")
        print("Example: python update_marks_sy4_od_etc.py etc_marksheet.pdf etc")
        print("Example: python update_marks_sy4_od_etc.py od_marksheet.pdf od")
        return

    pdf_input = sys.argv[1]
    subject_input = sys.argv[2].lower()

    # Support common subject variations
    if subject_input == "etc":
        target_subject = "etc"
    elif subject_input == "od":
        target_subject = "od"
    else:
        target_subject = subject_input
        print(f"Note: Using custom subject key '{target_subject}'")

    if not os.path.isabs(pdf_input):
        # Assume relative to the script location
        pdf_input = os.path.join(os.path.dirname(os.path.abspath(__file__)), pdf_input)
    
    marks = extract_marks_from_pdf(pdf_input)
    if marks:
        update_js_data(target_subject, marks)

if __name__ == "__main__":
    main()
