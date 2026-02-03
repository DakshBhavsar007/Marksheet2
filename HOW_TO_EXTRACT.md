# How to Extract Marks from PDF

This guide explains how to use the `update_marks_compiled.py` script to extract marks from a PDF file and update the `new_data.js` data file.

## Prerequisites

1.  **Python**: Ensure Python is installed.
2.  **Libraries**: You need `pdfplumber`. Install it if you haven't:
    ```bash
    pip install pdfplumber
    ```

## Files

-   `new_data.js`: The JavaScript file containing the student data (marks DB).
-   `update_marks_compiled.py`: The Python script that performs the extraction and update.
-   `Your_PDF_File.pdf`: The source PDF containing student results.

## How to Run

1.  Open a terminal (Command Prompt or PowerShell) and navigate to this folder:
    ```bash
    cd c:\Users\parul\Desktop\html\marksheet2
    ```

2.  Run the script with the PDF filename and the subject code:
    ```bash
    python update_marks_compiled.py <PDF_FILENAME> <SUBJECT_CODE>
    ```

### Subject Codes

-   `ps`: Probability & Statistics
-   `fsd`: Full Stack Development
-   `fcsp` or `python`: FCSP / Python
-   `de`: Digital Electronics
-   `etc`: Effective Technical Communication

### Example Command

To extract marks for **FSD** from a file named `Marksheet_SY4.pdf`:

```bash
python update_marks_compiled.py Marksheet_SY4.pdf fsd
```

To extract marks for **ETC** from a file named `Result.pdf`:

```bash
python update_marks_compiled.py Result.pdf etc
```

## How It Works

1.  The script reads the PDF and looks for a table with Enrollment Numbers and Marks.
2.  It extracts the mark (validating 'AB' as 0).
3.  It divides the extracted mark by **2**.
4.  It adds this value to the *existing* mark in `new_data.js` for that specific subject.
5.  It saves the updated data back to `new_data.js`.

> **Note:** The script assumes the PDF table format has the Enrollment Number in the 3rd column (index 2) and Marks in the 8th column (index 7).

## Special Case: SY4 Compiled Marksheet (No Division)

For the **SY4 Compiled Marksheet** (or any case where you explicitly do **NOT** want to divide the marks by 2), use the `update_marks_no_divide.py` script.

### Steps

1.  Open your terminal in the project folder:
    ```bash
    cd c:\Users\parul\Desktop\html\marksheet2
    ```

2.  Run the `update_marks_no_divide.py` script with the SY4 compiled PDF and the subject code (e.g., `etc`).

    **Syntax:**
    ```bash
    python update_marks_no_divide.py <COMPILED_PDF_FILENAME> <SUBJECT_CODE>
    ```

    **Example for ETC:**
    ```bash
    python update_marks_no_divide.py "SY4_COMPILED T1 to T3_MARKSHEET_CST_CSIT_MACP_CSE-CS_ODD_2025.pdf" etc
    ```

### How `update_marks_no_divide.py` Works

1.  Reads the PDF.
2.  Matches students by **NAME** (Column 7 / Index 6) instead of Enrollment Number.
3.  Extracted mark is added DIRECTLY to the existing mark (No division by 2).
4.  Updates `new_data.js`.
