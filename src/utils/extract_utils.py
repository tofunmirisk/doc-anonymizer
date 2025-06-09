from docx import Document
from dotenv import load_dotenv
load_dotenv(override=True)
import csv
import os
from config import SPOOL_DIR, OPENAI_API_KEY

# todo: extract lines from text box (shapes) and footnotes if present
def extract_lines(doc):
    """
    Extract lines from a DOCX file, treating line breaks within a paragraph as new lines.
    :param doc: A python-docx Document object
    :return: List of lines extracted from paragraphs and tables, with line breaks handled
    """
    def para_text_with_breaks(para):
        # Collect text, inserting \n for each line break within the paragraph
        text = ""
        for run in para.runs:
            text += run.text
            # Insert \n for each <w:br/> in the run
            for br in run._element.findall('.//w:br', run._element.nsmap):
                text += "\n"
        return text

    lines = []
    for para in doc.paragraphs:
        para_text = para_text_with_breaks(para).strip()
        if para_text:
            # Split on \n to treat line breaks as new lines
            lines.extend([line.strip() for line in para_text.split('\n') if line.strip()])
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para_text = para_text_with_breaks(para).strip()
                    if para_text:
                        lines.extend([line.strip() for line in para_text.split('\n') if line.strip()])
    return lines


def extract_text(doc):
    texts = []
    for para in doc.paragraphs:
        texts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    texts.append(para.text)
    for section in doc.sections:
        header = section.header
        for para in header.paragraphs:
            texts.append(para.text)
        for table in header.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        texts.append(para.text)
    return texts


def prepare_prompt(text):
    """
    Prepare the prompt for the LLM to extract sensitive values.
    :param text: The text content from the document
    :return: A formatted prompt string
    """

    return f"""
--- CONTRACT CONTENT START ---
{text}
--- CONTRACT CONTENT END ---
"""

def llm_filter(prompt, system_role=None, model="gpt-4o" ):
    import openai, os

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_role if system_role else "You are a helpful assistant for extracting sensitive values for anonymization."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0
    )
    import ast
    try:
        sensitive_list = ast.literal_eval(response.choices[0].message.content)
        return sensitive_list
    except Exception:
        return [response.choices[0].message.content.strip()]
    

def create_docx(paragraphs, filename):
    doc = Document()
    for p in paragraphs:
        doc.add_paragraph(p)
    doc.save(filename)

def write_sensitive_data_to_csv(sensitive_data: dict, csv_path: str, mode: str = 'w'):
    """
    Write the extracted sensitive data to a CSV file.
    """
    write_header = not (os.path.exists(csv_path) and mode == 'a')
    with open(csv_path, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(['EntityType', 'Values'])
        for entity_type, values in sensitive_data.items():
            if values:
                writer.writerow([entity_type.capitalize(), "\n".join(values)])
            else:
                writer.writerow([entity_type.capitalize(), ""])

def write_failed_to_csv(failed: dict, failed_csv_path: str, mode: str = 'w'):
    """ Write the failed extractions to a CSV file.
    Args:
        failed (dict): A dictionary where keys are document names and values are lists of failed entities.
        failed_csv_path (str): The path to the CSV file where failed extractions will be written.
        mode (str): The mode in which to open the file ('w' for write, 'a' for append).
    """
    write_header = not (os.path.exists(failed_csv_path) and mode == 'a')

    with open(failed_csv_path, mode, newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(['Document', 'FailedEntity'])
        for doc, entities in failed.items():
            for entity in entities:
                writer.writerow([doc, entity])
