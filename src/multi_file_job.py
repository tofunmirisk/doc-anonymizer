import os
import csv
import datetime
import glob
SPOOL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'spool'))

from extract import extract_sensitive_mapping
from generate import generate_pseudo_values
from replace import replace_words_in_docx
from utils.replace_utils import load_replacements_with_types
from docx import Document

def fetch_files():
    """
    Fetch all DOCX files from the spool directory.
    Returns a list of file paths.
    """
    return glob.glob(os.path.join(SPOOL_DIR, 'input', '*.docx'))

def extract_sensitive_multi_files():
    """
    Process each DOCX file and extract sensitive information.
    Merge sensitive_data for each file to have a single entity type index,
    joining all the values with '\n'.
    """
    docx_files = fetch_files()
    merged_data = {}

    for docx_file in docx_files:
        doc = Document(docx_file)
        sensitive_data = extract_sensitive_mapping(doc)
        for entity_type, values in sensitive_data.items():
            if entity_type not in merged_data:
                merged_data[entity_type] = []
            merged_data[entity_type].extend(values)

    # Join all values for each entity type with '\n'
    for entity_type in merged_data:
        merged_data[entity_type] = '\n'.join(merged_data[entity_type])

    return merged_data

if __name__ == "__main__":

    stage = input("Enter the stage (e.g., extract, generate, replace): ").strip().lower()

    if stage not in ['extract', 'generate', 'replace']:
        print("Invalid stage. Please enter 'extract', 'generate', or 'replace'.")
        exit(1)

    # Ensure spool and output directories exist
    os.makedirs(SPOOL_DIR, exist_ok=True)
    output_dir = os.path.join(SPOOL_DIR, 'output')
    os.makedirs(output_dir, exist_ok=True)

    if stage == 'extract':
            # write to a CSV file with timestamp prefix
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        extracted_csv = os.path.join(output_dir, f"{timestamp}-merged_sensitive_data.csv")
        
        print("Extracting sensitive data from DOCX files...")
        print(f"All files should be placed in the spool directory: {SPOOL_DIR}")
        merged_sensitive_data = extract_sensitive_multi_files()

        # Output the merged sensitive data
        for entity_type, values in merged_sensitive_data.items():
            print(f"{entity_type.capitalize()}: {values}")
        
        with open(extracted_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['EntityType', 'Values'])
            for entity_type, values in merged_sensitive_data.items():
                writer.writerow([entity_type.capitalize(), values])

    elif stage == 'generate':
        print("Generating pseudo values based on extracted data...")

        # Find the most recent {timestamp}-merged_sensitive_data.csv in output_dir
        pattern = os.path.join(output_dir, '*-merged_sensitive_data.csv')
        csv_files = glob.glob(pattern)
        if not csv_files:
            print("No merged_sensitive_data.csv files found in output directory.")
            exit(1)
        input_csv = max(csv_files, key=os.path.getctime)
        print(f"Using most recent extracted CSV: {input_csv}")

        # Create output filename based on input filename with suffix
        input_base = os.path.splitext(os.path.basename(input_csv))[0]
        output_csv = os.path.join(output_dir, f"{input_base}_pseudo_values.csv")
        generate_pseudo_values(input_csv, output_csv)

    elif stage == 'replace':
        print("Replacing sensitive data with pseudo values...")
        docx_files = fetch_files()
        if not docx_files:
            print("No DOCX files found in spool directory.")
            exit(1)

        pattern = os.path.join(output_dir, '*-merged_sensitive_data_pseudo_values.csv')
        csv_files = glob.glob(pattern)

        if not csv_files:
            print("No merged_sensitive_data_pseudo_values.csv files found in output directory.")
            exit(1)

        pseudo_csv = max(csv_files, key=os.path.getctime)
        print(f"Using most recent pseudo CSV: {pseudo_csv}")
        replacements = load_replacements_with_types(pseudo_csv)

        print(replacements)

        for docx_file in docx_files:
            doc = Document(docx_file)
            # Load pseudo values from the generated CSV
            doc = replace_words_in_docx(doc, replacements)

            # Save the modified document
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            save_filename = os.path.join(output_dir, f"{timestamp}_modified_{os.path.basename(docx_file)}")
            doc.save(save_filename)
            print(f"Document saved as '{save_filename}'.")
