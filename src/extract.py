import os
import csv
from docx import Document

from utils.extract_utils import extract_lines
from extract_identifiers.company_names import extract_company_names
from extract_identifiers.addresses import extract_addresses
from extract_identifiers.financial_values import extract_financial_values
from extract_identifiers.names import extract_names
from extract_identifiers.market_references import extract_market_references
from extract_identifiers.dates import extract_dates

SPOOL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'spool'))
os.makedirs(SPOOL_DIR, exist_ok=True)

def extract_sensitive_mapping(doc):
    lines = extract_lines(doc)
    companies = extract_company_names(lines)
    addresses = extract_addresses(lines)
    financial_values = extract_financial_values(lines)
    names = extract_names(lines)
    market_refs = extract_market_references(lines)
    dates = extract_dates(lines)

    return {
        "company": companies,
        "address": addresses,
        "financial_value": financial_values,
        "name": names,
        "market_reference": market_refs,
        "date": dates
    }

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

    sensitive_data = extract_sensitive_mapping(doc)
    print(f"Extracted sensitive data: {sensitive_data}")

    # Write results to CSV (one entity per line, next line separated)
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['EntityType', 'Value'])
        for entity_type, values in sensitive_data.items():
            writer.writerow([entity_type.capitalize(), "\n".join(values)])  

    # lines = extract_lines(doc)
    # texts = extract_text(doc)

    # Call each extractor
    # companies = extract_company_names(lines)
    # addresses = extract_addresses(lines)
    # financial_values = extract_financial_values(lines)
    # names = extract_names(lines)
    # market_refs = extract_market_references(lines)
    # dates = extract_dates(lines)

    # Write results to CSV (one entity per line, next line separated)
    # with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
    #     writer = csv.writer(csvfile)
    #     writer.writerow(['EntityType', 'Value'])
    #     writer.writerow(['Company', "\n".join(companies)])
    #     writer.writerow(['Address', "\n".join(addresses)])
    #     writer.writerow(['Financial', "\n".join(financial_values)])
    #     writer.writerow(['Name', "\n".join(names)])
    #     writer.writerow(['Market Reference', "\n".join(market_refs)])
    #     writer.writerow(['Date', "\n".join(dates)])

    print(f"Extraction complete. Results written to {csv_path}")