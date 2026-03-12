import fitz
import os

def pdf_to_images(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150)
            output_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
            pix.save(output_path)
            print(f"Saved: {output_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    pdf_to_images(r"c:\Workspaces\aws_practice\documents\화면 설계서.pdf", r"c:\Workspaces\aws_practice\tmp_pdf_images")
