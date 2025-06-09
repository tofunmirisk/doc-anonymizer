import os
import csv
from docx import Document
from config import SPOOL_DIR, logger

from utils.extract_utils import extract_lines
from extract_identifiers.company_names import extract_company_names
from extract_identifiers.addresses import extract_addresses
from extract_identifiers.financial_values import extract_financial_values
from extract_identifiers.names import extract_names
from extract_identifiers.market_references import extract_market_references
from extract_identifiers.dates import extract_dates
from utils.extract_utils import write_sensitive_data_to_csv, write_failed_to_csv

def extract_sensitive_mapping(docx_file: str, extractors_list: list = None) -> tuple:
    """
    Extract sensitive information from a DOCX document using various extractors.    
    Returns a tuple: (dict of extracted values, dict of failed extractions).
    """
    doc = Document(docx_file)
    lines = extract_lines(doc)

    all_extractors = {
        "company": extract_company_names,
        "address": extract_addresses,
        "financial_value": extract_financial_values,
        "name": extract_names,
        "market_reference": extract_market_references,
        "date": extract_dates
    }

    extractors = all_extractors
    if extractors_list:
        extractors = {key: all_extractors[key] for key in extractors_list if key in all_extractors}

    results = {}
    failed = {}
    logger.info(f"Extracting from {docx_file} using extractors: {list(extractors.keys())}")
    for key, extractor in extractors.items():
        try:
            results[key] = extractor(lines)
        except Exception as e:
            logger.error(f"Error extracting {key} from {docx_file}: {e}")
            results[key] = []
            failed.setdefault(docx_file, []).append(key)
    return results, failed

def retry_failed_extractions(failed: dict) -> tuple:
    """
    Retry failed extractions for the given documents/entities.
    Returns merged (results, failed) tuple.
    """
    results = {}
    still_failed = {}
    for doc_path, entity_types in failed.items():
        for entity_type in entity_types:
            logger.info(f"Retrying extraction for {entity_type} in {doc_path}")
            retry_results, retry_failed = extract_sensitive_mapping(doc_path, extractors_list=[entity_type])
            if entity_type in retry_results and retry_results[entity_type]:
                results.setdefault(doc_path, {})[entity_type] = retry_results[entity_type]
            else:
                still_failed.setdefault(doc_path, []).append(entity_type)
    return results, still_failed

if __name__ == "__main__":
    logger.info(f"All files should be placed in the spool directory: {SPOOL_DIR}")

    mode = input("Enter the mode (extract/retry): ").strip().lower()
    if mode not in ['extract', 'retry']:
        logger.error("Invalid mode. Please enter 'extract' or 'retry'.")
        exit(1)

    if mode == 'extract':
        docx_filename = input("Enter the DOCX filename (in spool directory): ").strip()
        docx_path = os.path.join(SPOOL_DIR, docx_filename)
        if not os.path.isfile(docx_path):
            logger.error("File not found in spool directory.")
            exit(1)
        csv_filename = input("Enter the output CSV filename (in spool directory): ").strip()
        csv_path = os.path.join(SPOOL_DIR, csv_filename)

        sensitive_data, failed = extract_sensitive_mapping(docx_path)
        logger.info(f"Extracted sensitive data: {sensitive_data}")
        if failed:
            logger.warning(f"Some extractions failed: {failed}")
            failed_csv_path = os.path.join(SPOOL_DIR, "failed_" + csv_filename)
            write_failed_to_csv(failed, failed_csv_path)
            logger.info(f"Failed extractions written to {failed_csv_path}")

        write_sensitive_data_to_csv(sensitive_data, csv_path)
        logger.info(f"Extraction complete. Results written to {csv_path}")

    elif mode == 'retry':
        csv_filename = input("Enter the output CSV filename (in spool directory): ").strip()
        csv_path = os.path.join(SPOOL_DIR, csv_filename)
        logger.info(f"Retrying failed extractions from {csv_path}...")
        if not os.path.isfile(csv_path):
            logger.error("File not found in spool directory.")
            exit(1)

        # get base directory of the CSV file
        base_dir = os.path.dirname(csv_path)
        file_name = os.path.basename(csv_path)

        failed_csv_path = os.path.join(base_dir, "failed_" + file_name)
        if not os.path.isfile(failed_csv_path):
            logger.error("No failed extractions found. Please run extraction first.")
            exit(1)

        failed = {}
        with open(failed_csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip header
            for row in reader:
                if row and len(row) == 2:
                    failed.setdefault(row[0], []).append(row[1])

        retry_results, still_failed = retry_failed_extractions(failed)
        # Merge retry_results into existing CSV (append mode)
        for doc, entity_dict in retry_results.items():
            write_sensitive_data_to_csv(entity_dict, csv_path, mode='a')
        logger.info(f"Retry complete. Results appended to {csv_path}")

        if still_failed:
            logger.warning(f"Some extractions still failed: {still_failed}")
            write_failed_to_csv(still_failed, failed_csv_path)
            logger.info(f"Failed extractions written to {failed_csv_path}")
        else:
            # remove the failed CSV if all extractions were successful
            if os.path.exists(failed_csv_path):
                os.remove(failed_csv_path)
                logger.info(f"Removed failed extractions file: {failed_csv_path}")
            logger.info("All extractions successful.")

