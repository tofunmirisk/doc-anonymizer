import csv
import os
from config import SPOOL_DIR, logger

# ... (same word banks as before) ...
# Input CSV format: 
# Company, "compnayA\ncompnayB\ncompnayC"
# Names, "Mr. John Doe\nDr. Jane Smith"
# Financial, "B1234\nB5678"
# Addresses, "123 Main St, City, Country\n456 Elm St, City, Country"
# Market References, "Ref123\nRef456"
# Dates, "2023-01-01\n2023-02-02"

# create a method that expands the input csv into multidimensional array type,original

SPOOL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'spool'))
os.makedirs(SPOOL_DIR, exist_ok=True)

def expand_csv(input_csv):
    """
    Reads an input CSV where each row is: Type, "value1\\nvalue2\\nvalue3"
    Returns a generator of unique (type, original) tuples, one for each value.
    """
    seen = set()
    with open(input_csv, newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        for row in reader:
            if len(row) < 2:
                continue
            type_name = row[0].strip()
            values = row[1].strip()
            if values.startswith('"') and values.endswith('"'):
                values = values[1:-1]
            for value in values.split('\n'):
                value = value.strip()
                key = (type_name, value)
                if value and key not in seen:
                    seen.add(key)
                    yield key

def generate_text(expanded: list) -> str:
    text = ""
    for elem in expanded[1:]:  # Skip the first element which is the header
        text += f"{elem[0]}|{elem[1]}\n"
    return text

def generate_expanded_from_text(text: str) -> list:
    """
    Converts a text representation of expanded values back into a list of tuples.
    Each line in the text should be formatted as: EntityType|original_value
    """
    expanded = []
    lines = text.strip().split('\n')
    for line in lines:
        if '|' in line:
            entity_type, original_value = line.split('|', 1)
            expanded.append((entity_type.strip(), original_value.strip()))
    return expanded

def invoke_llm(text: str) -> str:
    """
    Generates a pseudo value based on the original value.
    This is a simple example that replaces letters with random characters.
    """
    logger.info(f"Generating pseudo values for the following text:\n{text}")
    from utils.extract_utils import llm_filter
    prompt = f"""For each EntityType|Value pair in the provided text, generate a pseudo-value of the EntityType. Maintain original context and format, ensuring consistency with other generated pseudo-values. Output as EntityType|original|pseudo using | as the separator:
    \n{text}
    """
    pseudo_value = llm_filter(prompt,
                system_role="You are an expert at generating consistent pseudo-content based on entity types and original values, maintaining context and recurrence",
                model="gpt-4o"
    )
    return pseudo_value

class PseudoValueGenerator:
    def __init__(self, expanded, batch_size=100):
        self.expanded = expanded
        self.batch_size = batch_size
        self.failed = {}

    def __iter__(self):
        batch = []
        batch_num = 1
        for item in self.expanded:
            batch.append(item)
            if len(batch) == self.batch_size:
                yield from self._process_batch(batch, batch_num)
                batch = []
                batch_num += 1
        if batch:
            yield from self._process_batch(batch, batch_num)

    def _process_batch(self, batch, batch_num):
        text = generate_text(batch)
        try:
            pseudo_value = invoke_llm(text)
        except Exception as e:
            self.failed[batch_num] = text
            logger.error(f"Failed to generate pseudo values for batch {batch_num}: {e}")
            return
        pseudo_lines = [line.strip() for line in pseudo_value[0].split('\n') if line.strip() and "`" not in line.strip()]
        logger.debug(f"Generated pseudo values for batch {batch_num}: {pseudo_lines}")
        yield pseudo_lines

def generate_pseudo_values(input_csv: str, output_csv: str) -> None:
    """
    Reads an input CSV, expands it, generates text, and then generates pseudo values in batches.
    Maintains context for LLM across batches. Appends all results to the same output file.
    """
    expanded = expand_csv(input_csv)
    pseudo_value_gen = PseudoValueGenerator(expanded)

    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='|')
        for elem in pseudo_value_gen:
            for row in elem:
                writer.writerow([col.replace('"', '') for col in row.split('|')])

    if pseudo_value_gen.failed:
        logger.warning("Some batches failed to generate pseudo values. See details below:")
        output_csv_name = os.path.basename(output_csv)
        output_csv_dir = os.path.dirname(output_csv)
        failed_csv = os.path.join(output_csv_dir, f'failed_batches_{output_csv_name}')
        with open(failed_csv, 'w', newline='', encoding='utf-8') as failed_file:
            writer = csv.writer(failed_file, delimiter='|')
            writer.writerow(['BatchNumber', 'Text'])
            for batch_num, text in pseudo_value_gen.failed.items():
                logger.debug(f"Batch {batch_num} failed with text: {text}")
                writer.writerow([batch_num, text])

def retry_failed_batches(failed_csv, output_csv: str):
    """
    Retry generating pseudo values for failed batches.
    Returns a generator of pseudo value rows.
    """
    if not failed_csv or not os.path.isfile(failed_csv):
        logger.error("No failed batches CSV file provided or file does not exist.")
        return

    with open(failed_csv, 'r', newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        next(reader, None)  # Skip header
        failed = {row[0]: row[1] for row in reader if row and len(row) > 1}

    with open(output_csv, 'a', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile, delimiter='|')
        for batch_num, text in failed.items():
            try:
                expanded = generate_expanded_from_text(text)
                pseudo_value_gen = PseudoValueGenerator(expanded)
                for elem in pseudo_value_gen:
                    for row in elem:
                        writer.writerow([col.replace('"', '') for col in row.split('|')])
                        yield row  # Yield each pseudo value row
            except Exception as e:
                logger.error(f"Failed to retry batch {batch_num}: {e}")

if __name__ == "__main__":

    mode = input("Enter the mode (generate/retry): ").strip().lower()
    if mode not in ['generate', 'retry']:
        logger.error("Invalid mode. Please enter 'generate' or 'retry'.")
        exit(1)

    if mode == 'generate':
        logger.info(f"All files should be placed in the spool directory: {SPOOL_DIR}")
        input_csv_name = input("Enter the input CSV filename (in spool directory): ").strip()
        input_csv = os.path.join(SPOOL_DIR, input_csv_name)
        if not os.path.isfile(input_csv):
            logger.error("File not found in spool directory.")
            exit(1)
        output_csv_name = input("Enter the output CSV filename (will be placed in spool directory): ").strip()
        output_csv = os.path.join(SPOOL_DIR, output_csv_name)
        generate_pseudo_values(input_csv, output_csv)

    if mode == 'retry':
        output_csv_name = input("Enter the output CSV filename (will be placed in spool directory): ").strip()
        output_csv = os.path.join(SPOOL_DIR, output_csv_name)
        # derive failed CSV path from output CSV path and filename
        output_csv_name = os.path.basename(output_csv)
        output_csv_dir = os.path.dirname(output_csv)
        failed_csv = os.path.join(output_csv_dir, f'failed_batches_{output_csv_name}')
        retry_failed_batches(failed_csv, output_csv)
