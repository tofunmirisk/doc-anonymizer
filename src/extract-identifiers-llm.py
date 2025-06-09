import os
import csv
from docx import Document
import openai

from extract_identifiers.extract_sensitive_mapping_llm import extract_sensitive_mapping_llm

SPOOL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'spool'))

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

def extract_sensitive_list_llm(text, openai_api_key, model="gpt-4o"):
    prompt = f"""
You are an expert in document anonymization.

Given the following contract content, extract all sensitive or identifying values (company names, brokers, UMRs, addresses, clause references, monetary values, etc.) as they appear in the text.
- Only extract the exact values as they appear.
- Do NOT include variants or alternate forms.
- Return your answer as a valid Python list of strings.

--- CONTRACT CONTENT START ---
{text}
--- CONTRACT CONTENT END ---
"""
    client = openai.OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant for extracting sensitive values for anonymization."},
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

if __name__ == "__main__":
    print(f"All files should be placed in the spool directory: {SPOOL_DIR}")
    docx_filename = input("Enter the DOCX filename (in spool directory): ").strip()
    docx_path = os.path.join(SPOOL_DIR, docx_filename)
    if not os.path.isfile(docx_path):
        print("File not found in spool directory.")
        exit(1)
    csv_filename = input("Enter the output CSV filename (in spool directory): ").strip()
    csv_path = os.path.join(SPOOL_DIR, csv_filename)
    doc = Document(docx_path)
    texts = extract_text(doc)

    print(f"Extraction complete. Results written to {csv_path}")

    # --- LLM Extraction: Only extract sensitive details, not variants ---
    api_key = "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"  # Your OpenAI API key

    # Join texts for LLM input
    contract_text = "\n".join(texts)

    sensitive_details = extract_sensitive_list_llm(contract_text, api_key)
    print(sensitive_details)

    # Write LLM sensitive details result to a new CSV file
    llm_csv_path = os.path.join(SPOOL_DIR, csv_filename)
    with open(llm_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['SensitiveValue'])
        for value in sensitive_details:
            writer.writerow([value])

    print(f"LLM sensitive details written to {llm_csv_path}")