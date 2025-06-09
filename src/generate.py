import csv
import random
import string
import json
import os
import re

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

def expand_csv(input_csv) -> list:
    """
    Reads an input CSV where each row is: Type, "value1\\nvalue2\\nvalue3"
    Returns a list of (type, original) tuples, one for each value.
    """
    expanded = []
    with open(input_csv, newline='', encoding='utf-8') as infile:
        reader = csv.reader(infile)
        for row in reader:
            if len(row) < 2:
                continue
            type_name = row[0].strip()
            # Remove surrounding quotes if present
            values = row[1].strip()
            if values.startswith('"') and values.endswith('"'):
                values = values[1:-1]
            for value in values.split('\n'):
                value = value.strip()
                if value:
                    expanded.append((type_name, value))
    return expanded

def generate_text(expanded: list) -> str:
    text = ""
    for elem in expanded[1:]:  # Skip the first element which is the header
        text += f"{elem[0]}|{elem[1]}\n"
    return text

def invoke_llm(text: str) -> str:
    """
    Generates a pseudo value based on the original value.
    This is a simple example that replaces letters with random characters.
    """
    print(f"Generating pseudo values for the following text:\n{text}")
        # Use LLM to filter and clean up the company names
    from utils.extract_utils import llm_filter
    prompt = f"""For each EntityType|Value pair in the provided text, generate a pseudo-value of the EntityType. Maintain original context and format, ensuring consistency with other generated pseudo-values. Output as EntityType|original|pseudo using | as the separator:
    \n{text}
    """
    pseudo_value = llm_filter(prompt,
                system_role="You are an expert at generating consistent pseudo-content based on entity types and original values, maintaining context and recurrence",
                model="gpt-4o"
    )
    return pseudo_value

def pseudo_value_generator(expanded: list, batch_size: int = 100) -> GeneratorExit: # type: ignore
    """
    Generates pseudo values for each (type, original) pair in the expanded list.
    Returns a list of pseudo values.
    """
    total = len(expanded)

    for start in range(0, total, batch_size):
        batch = expanded[start:start+batch_size]
        text = generate_text(batch)
        pseudo_value = invoke_llm(text)
        
        # Split the response into lines and filter out empty lines
        pseudo_lines = [line.strip() for line in pseudo_value[0].split('\n') if line.strip() and "`" not in line.strip()]
        print(f"[DEBUG] Generated pseudo values for batch {start // batch_size + 1}: {pseudo_lines}")
        yield pseudo_lines

def generate_pseudo_values(input_csv: str, output_csv: str) -> None:
    """
    Reads an input CSV, expands it, generates text, and then generates pseudo values in batches.
    Maintains context for LLM across batches. Appends all results to the same output file.
    """
    expanded = expand_csv(input_csv)
    pseudo_value_gen = pseudo_value_generator(expanded)

    # Open output file once for writing all batches
    with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)

        # Write each pseudo row to the output file
        for elem in pseudo_value_gen:
            for row in elem:
                writer.writerow([row.replace('"', '')])

if __name__ == "__main__":
    print(f"All files should be placed in the spool directory: {SPOOL_DIR}")
    input_csv_name = input("Enter the input CSV filename (in spool directory): ").strip()
    input_csv = os.path.join(SPOOL_DIR, input_csv_name)
    if not os.path.isfile(input_csv):
        print("File not found in spool directory.")
        exit(1)
    output_csv_name = input("Enter the output CSV filename (will be placed in spool directory): ").strip()
    output_csv = os.path.join(SPOOL_DIR, output_csv_name)
    generate_pseudo_values(input_csv, output_csv)

