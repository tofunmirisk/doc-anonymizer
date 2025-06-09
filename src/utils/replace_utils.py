def create_document():
    from docx import Document
    return Document()

def add_paragraph(doc, text):
    doc.add_paragraph(text)

def save_document(doc, filename):
    doc.save(filename)

import csv
import re
from docx.shared import Inches

def load_replacements(csv_path):
    """
    Loads a CSV file with two columns: original|fictitious (pipe-delimited)
    Returns a dictionary {original: fictitious}, skipping pairs where both are identical.
    """
    replacements = {}
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='|')
        for row in reader:
            if len(row) >= 2:
                original, fictitious = row[0].strip(), row[1].strip()
                if original and fictitious and original != fictitious:
                    replacements[original] = fictitious
    return replacements

def load_replacements_with_types(csv_path):
    """
    Loads a CSV file with three columns: type|original|fictitious (pipe-delimited)
    Returns a flat dictionary {original: fictitious}, skipping pairs where both are identical.
    Handles the case where all entries are in the first row.
    """
    replacements = {}
    print(f"[DEBUG] Loading replacements from {csv_path}")
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter='|')
        rows = list(reader)
        # If all entries are in the first row, split by '\n'
        if len(rows) == 1 and '\n' in rows[0][0]:
            # Split the first cell by newlines to get each row
            split_rows = [r.split('|') for r in rows[0][0].split('\n') if r.strip()]
        else:
            split_rows = rows
        for row in split_rows:
            print(f"[DEBUG] Processing row: {row}")
            if len(row) >= 3:
                type_name, original, fictitious = row[0].strip(), row[1].strip(), row[2].strip()
                print(f"[DEBUG] Processing row: type={type_name}, original='{original}', fictitious='{fictitious}'")
                if original and fictitious and original != fictitious:
                    replacements[original] = fictitious
        print(f"[DEBUG] Loaded replacements: {replacements} ")
    return replacements

def replace_words_in_docx(doc, replacements):
    """
    Replaces all occurrences of words/phrases in the replacements dict within the docx Document,
    including headers and tables. Replacements are whole-word only.
    Preserves all formatting and styles.
    Saves to output_file if provided, otherwise appends '_output' to original_file and saves there.
    """
    import re
    def is_simple_word(word):
        # Only letters, numbers, or underscores, no spaces or punctuation
        return re.match(r'^\w+$', word) is not None

    patterns = {}
    for word in replacements:
        if is_simple_word(word):
            patterns[word] = re.compile(rf'\b{re.escape(word)}\b')
        else:
            patterns[word] = re.compile(re.escape(word))

    def replace_in_runs(paragraph, patterns):
        # If there are no runs, nothing to do
        if not paragraph.runs:
            return
        # Join all run texts to get the full paragraph text
        full_text = ''.join(run.text for run in paragraph.runs)
        replaced_text = full_text
        for word, pattern in patterns.items():
            replaced_text = pattern.sub(replacements[word], replaced_text)
        if full_text != replaced_text:
            print(f"[DEBUG] Paragraph before: '{full_text}' | Paragraph after: '{replaced_text}'")
        # Assign replaced text to the first run, clear the rest
        if paragraph.runs:
            paragraph.runs[0].text = replaced_text
            for run in paragraph.runs[1:]:
                run.text = ''

    # # Replace in main document paragraphs
    for para in doc.paragraphs:
        replace_in_runs(para, patterns)

    # # Replace in main document tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    replace_in_runs(para, patterns)

    # Save to output_file
    return doc

# def replace_words_in_docx_with_headers(doc, replacements):
    # Replace in headers (all sections)
    for section in doc.sections:
        # Always process all header types
        for header in [section.header, getattr(section, 'first_page_header', None), getattr(section, 'even_page_header', None)]:
            if header is None:
                continue
            for para in header.paragraphs:
                print(f"[DEBUG] Header paragraph before: '{''.join(run.text for run in para.runs)}'")
                replace_in_runs(para, patterns)
                print(f"[DEBUG] Header paragraph after: '{''.join(run.text for run in para.runs)}'")
            for table in header.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for para in cell.paragraphs:
                            print(f"[DEBUG] Header table cell before: '{''.join(run.text for run in para.runs)}'")
                            replace_in_runs(para, patterns)
                            print(f"[DEBUG] Header table cell after: '{''.join(run.text for run in para.runs)}'")

        # Edge case: process textboxes in headers (w:txbxContent) using lxml
        # This is NOT the normal case, but handles text in header shapes/textboxes
        try:
            from lxml import etree
            W_NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
            for header in [section.header, getattr(section, 'first_page_header', None), getattr(section, 'even_page_header', None)]:
                if header is None:
                    continue
                xml = header._element
                # Find all w:txbxContent elements (textboxes) using explicit namespace
                for txbx in xml.findall('.//' + W_NS + 'txbxContent'):
                    for t in txbx.findall('.//' + W_NS + 't'):
                        print(f"[DEBUG][EDGE CASE] Textbox tag: {t.tag}")
                        print(f"[DEBUG][EDGE CASE] Textbox text: {t.text}")
                        print(f"[DEBUG][EDGE CASE] Textbox XML: {etree.tostring(t, pretty_print=True, encoding='unicode')}")

                        # Remove <w:t> tag if its text matches a word/phrase to be filtered out (replacement is empty string)
                        remove_tag = False
                        orig_text = t.text
                        replaced_text = orig_text
                        for word, pattern in patterns.items():
                            if replacements[word] == '':
                                # If the whole tag matches the word/phrase, mark for removal
                                if orig_text == word:
                                    remove_tag = True
                                # If the word/phrase is a substring, remove it from the text
                                replaced_text = pattern.sub('', replaced_text)
                            else:
                                replaced_text = pattern.sub(replacements[word], replaced_text)
                        if remove_tag:
                            print(f"[DEBUG][EDGE CASE] Removing <w:t> tag with text: '{orig_text}'")
                            parent = t.getparent()
                            parent.remove(t)
                            continue
                        if orig_text != replaced_text:
                            print(f"[DEBUG][EDGE CASE] Textbox text before: '{orig_text}' | after: '{replaced_text}'")
                        t.text = replaced_text
        except ImportError:
            print("[WARNING] lxml not installed, skipping edge case textbox replacement in headers.")
        except Exception as e:
            print(f"[WARNING] Error processing header textboxes: {e}")