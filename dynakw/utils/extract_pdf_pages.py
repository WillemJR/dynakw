
import os
import fitz  # PyMuPDF


def extract_pages_pymupdf(input_pdf, output_pdf, start_page, end_page):
    """
    Extract specific pages using PyMuPDF and save as new PDF.
    Pages are 0-indexed.
    """
    doc = fitz.open(input_pdf)

    # Create new document with selected pages
    new_doc = fitz.open()

    for page_num in range(start_page, min(end_page + 1, doc.page_count)):
        new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    new_doc.save(output_pdf)
    new_doc.close()
    doc.close()

    print(f"Extracted pages {start_page}-{end_page} to {output_pdf}")


# Example usage
if __name__ == "__main__":
    input_pdf = "$HOME/Documents/DYNA/LS-DYNA_Manual_Volume_I_R14.pdf"
    expanded_path = os.path.expandvars(input_pdf)

    print("\n=== Extracting Page Range ===")
    extract_pages_pymupdf(expanded_path, "section_solid.pdf", 3471, 3492)

    print("\nAll extractions complete! Upload any of these PDFs to Claude.")
