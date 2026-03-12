import fitz
import sys

def extract_text(pdf_path):
    print(f"--- Reading: {pdf_path} ---")
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        print(text[:4000] + "...\n" if len(text) > 4000 else text + "\n")
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

if __name__ == "__main__":
    extract_text(r"c:\Workspaces\aws_practice\documents\화면 설계서.pdf")
