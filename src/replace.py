# main.py

import os
from docx import Document
from utils.replace_utils import load_replacements, replace_words_in_docx

SPOOL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'spool'))

def main():
    print("Welcome to the DOCX Word Replacer!")
    print(f"All files should be placed in the spool directory: {SPOOL_DIR}")

    # Ensure spool directory exists
    os.makedirs(SPOOL_DIR, exist_ok=True)

    # Get DOCX file path
    docx_filename = input("Enter the DOCX filename (in spool directory): ").strip()
    docx_path = os.path.join(SPOOL_DIR, docx_filename)
    if not os.path.isfile(docx_path):
        print("File not found in spool directory.")
        return

    # Get replacement table path (CSV)
    replacements_filename = input("Enter the replacements CSV filename (in spool directory): ").strip()
    replacements_path = os.path.join(SPOOL_DIR, replacements_filename)
    if not os.path.isfile(replacements_path):
        print("Replacement table not found in spool directory.")
        return

    # Load document and replacements
    doc = Document(docx_path)
    replacements = load_replacements(replacements_path)

    # Replace words
    replace_words_in_docx(doc, replacements)

    # Save the modified document
    save_filename = input("Enter the filename to save the modified document (without .docx, in spool directory): ").strip() + ".docx"
    save_path = os.path.join(SPOOL_DIR, save_filename)
    doc.save(save_path)
    print(f"Document saved as '{save_path}'.")

if __name__ == "__main__":
    main()