
import pypdf
import argparse
from typing import Dict


def extract_chapter_by_bookmark(pdf_path, chapter_name):
    """
    Extracts a chapter from the LS-Dyna manual.

    The Dyna manual is tricky:Items like CONTACT requires another layer.
    """

    print('Extracting', chapter_name, 'from', pdf_path)

    start_page = None
    end_page = None
    with open(pdf_path, 'rb') as file:
        reader = pypdf.PdfReader(file)

        bookmarks = reader.outline

        for i, bookmark in enumerate(bookmarks):
            if isinstance(bookmark, list):
                for j, bookmark2 in enumerate(bookmark):
                    if isinstance(bookmark2, Dict):
                        if start_page is not None and end_page is None:
                            end_page = reader.get_destination_page_number(
                                bookmark2)
                            writer = pypdf.PdfWriter()
                            for page_num in range(start_page, end_page):
                                writer.add_page(reader.pages[page_num])
                            return writer

                        if '/Title' in bookmark2.keys():
                            if bookmark2['/Title'] == chapter_name:
                                start_page = reader.get_destination_page_number(
                                    bookmark2)

    if start_page is not None and end_page is None:
        writer = pypdf.PdfWriter()
        end_page = len(reader.pages)
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])
        return writer

    return None


def main():
    parser = argparse.ArgumentParser(
        description="Extract a chapter from a PDF file using its bookmark name.")
    parser.add_argument("pdf_path", help="Path to the input PDF file.")
    parser.add_argument(
        "chapter_name", help="The exact name of the chapter bookmark to extract.")
    parser.add_argument(
        "-o", "--output", help="Path to the output PDF file. Defaults to the chapter name with a .pdf extension.")
    args = parser.parse_args()

    output_filename = args.output
    if not output_filename:
        # Sanitize the chapter name to create a valid filename
        sanitized_name = "".join(
            c for c in args.chapter_name if c.isalnum() or c == '_')
        output_filename = f"{sanitized_name}.pdf"

    chapter_name = args.chapter_name
    if chapter_name[0] != '*':
        chapter_name = '*' + chapter_name

    writer = extract_chapter_by_bookmark(args.pdf_path, chapter_name)

    if writer:
        with open(output_filename, 'wb') as output_file:
            writer.write(output_file)
        print(
            f"Successfully extracted '{args.chapter_name}' to '{output_filename}'")
    else:
        print(
            f"Error: Could not find chapter '{args.chapter_name}' in '{args.pdf_path}'")


if __name__ == "__main__":
    main()
