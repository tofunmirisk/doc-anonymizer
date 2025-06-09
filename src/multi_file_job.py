import os
import csv
import datetime
import glob
from config import SPOOL_DIR, OUTPUT_DIR, INPUT_DIR, logger

from extract import extract_sensitive_mapping
from generate import generate_pseudo_values
from replace import replace_words_in_docx
from utils.replace_utils import load_replacements_with_types
from utils.extract_utils import write_sensitive_data_to_csv, write_failed_to_csv
from docx import Document

def fetch_files():
    """
    Fetch all DOCX files from the spool directory.
    Returns a list of file paths.
    """
    return glob.glob(os.path.join(INPUT_DIR, '*.docx'))

def extract_sensitive_mapping_gen(docx_files):
    """
    Extract sensitive information from the document using a generative approach.
    """
    for docx_file in docx_files:
        yield extract_sensitive_mapping(docx_file)
    

def extract_sensitive_multi_files(docx_files, extracted_csv, failed_csv):
    """
    Process each DOCX file and extract sensitive information.
    Merge sensitive_data for each file to have a single entity type index,
    joining all the values with '\n'.
    """

    for sensitive_data, failed in extract_sensitive_mapping_gen(docx_files):
        write_sensitive_data_to_csv(sensitive_data, extracted_csv, mode='a')
        if failed:
            write_failed_to_csv(failed, failed_csv, mode='a')

    logger.info(f"Sensitive data extracted and written to {extracted_csv}")

if __name__ == "__main__":

    input_entry = input(
        "Enter the stage (extract, generate, replace) or stage:mode (e.g., extract:retry):\n"
        "  extract   - Extract sensitive data from all DOCX files in spool/input/\n"
        "  generate  - Generate pseudo values from the most recent extracted CSV\n"
        "  replace   - Replace sensitive data in DOCX files using the most recent pseudo values CSV\n"
    ).strip().lower()
    
    stage, mode = input_entry.split(":") if ":" in input_entry else (input_entry, None)

    if stage not in ['extract', 'generate', 'replace']:
        logger.error("Invalid stage. Please enter 'extract', 'generate', or 'replace'.")
        exit(1)

    # Ensure spool and output directories exist
    output_dir = OUTPUT_DIR

    if stage == 'extract':
        docx_files = fetch_files()    
        if not docx_files:
            logger.error("No DOCX files found in spool directory.")
            logger.info(f"All files should be placed in the spool directory: {SPOOL_DIR}/input")
            exit(1)
        
        # write to a CSV file with timestamp prefix
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_merged_sensitive_data.csv"

        extracted_csv = os.path.join(output_dir, f"{filename}")
        failed_csv = os.path.join(output_dir, f"failed_{filename}")
        logger.info(f"Extracting sensitive data to {extracted_csv}...")
        logger.info(f"Failed extractions will be logged to {failed_csv}...")
        
        # Extract sensitive data from DOCX files
        extract_sensitive_multi_files(docx_files, extracted_csv, failed_csv)

        logger.info("Extracted sensitive data from DOCX files...")
    
    elif stage == 'generate':
        logger.info("Generating pseudo values based on extracted data...")

        # Find the most recent *_merged_sensitive_data.csv in output_dir
        pattern = os.path.join(output_dir, '*_merged_sensitive_data.csv')
        csv_files = glob.glob(pattern)
        if not csv_files:
            logger.error("No merged_sensitive_data.csv files found in output directory.")
            exit(1)
        input_csv = max(csv_files, key=os.path.getctime)
        logger.info(f"Using most recent extracted CSV: {input_csv}")

        # Create output filename based on input filename with suffix
        input_base = os.path.splitext(os.path.basename(input_csv))[0]
        output_csv = os.path.join(output_dir, f"{input_base}_pseudo_values.csv")
        generate_pseudo_values(input_csv, output_csv)

    elif stage == 'replace':
        logger.info("Replacing sensitive data with pseudo values...")
        docx_files = fetch_files()
        if not docx_files:
            logger.error("No DOCX files found in spool directory.")
            exit(1)

        pattern = os.path.join(output_dir, '*_merged_sensitive_data_pseudo_values.csv')
        csv_files = glob.glob(pattern)

        if not csv_files:
            logger.error("No merged_sensitive_data_pseudo_values.csv files found in output directory.")
            exit(1)

        pseudo_csv = max(csv_files, key=os.path.getctime)
        logger.info(f"Using most recent pseudo CSV: {pseudo_csv}")
        replacements = load_replacements_with_types(pseudo_csv)

        logger.debug(replacements)

        for docx_file in docx_files:
            doc = Document(docx_file)
            # Load pseudo values from the generated CSV
            doc = replace_words_in_docx(doc, replacements)

            # Save the modified document
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            save_filename = os.path.join(output_dir, f"{timestamp}_anon_{os.path.basename(docx_file)}")
            doc.save(save_filename)
            logger.info(f"Document saved as '{save_filename}'.")
