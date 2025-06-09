# python-docx-project

This project provides tools to anonymize and pseudonymize sensitive information in Word documents using the `python-docx` library and LLM-based pseudo value generation.

## What It Does

- Extracts sensitive entities (company names, financials, dates, names, market references, phone numbers, addresses) from `.docx` files.
- Generates consistent pseudo values for these entities using an LLM.
- Replaces sensitive data in Word documents with pseudo values.
- Supports batch processing and incremental CSV output.

## Installation

1. **Clone the repository**  
   ```sh
   git clone <repo-url>
   cd python-docx-project
   ```

2. **Install dependencies**  
   ```sh
   pip install -r requirements.txt
   ```

3. **(Optional) Set up your `.env` file**  
   Create a `.env` file in the project root and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your-key-here
   ```

## Setup

1. **Create the spool directory structure**  
   ```sh
   mkdir -p spool/input
   mkdir -p spool/output
   ```

2. **Place your `.docx` files to process in `spool/input/`**

## Usage

All entry points are in the `src/` directory. Run each as a module from the project root.

### 1. Extract Sensitive Data

Extracts sensitive entities from all `.docx` files in `spool/input/` and writes a merged CSV to `spool/output/`.

```sh
python -m src.multi_file_job
```
- When prompted, enter: `extract`

### 2. Generate Pseudo Values

Generates pseudo values for the extracted data and writes to a new CSV in `spool/output/`.

```sh
python -m src.multi_file_job
```
- When prompted, enter: `generate`
- The app will automatically use the most recent extracted CSV as input.

### 3. Replace Sensitive Data in Documents

Replaces sensitive data in `.docx` files in `spool/input/` using the most recent pseudo values CSV.

```sh
python -m src.multi_file_job
```
- When prompted, enter: `replace`
- Modified documents will be saved in `spool/output/`.

### 4. Manual Entry Points

You can also run the following scripts directly for more granular control:

- **generate.py**: For generating pseudo values from a specific CSV.
  ```sh
  python src/generate.py
  ```
  Follow the prompts to specify input and output CSV files.

- **extract.py**: For extracting sensitive data from a single document.
  ```sh
  python src/extract.py
  ```

## Features

- Batch processing for large files
- Incremental CSV output for memory efficiency
- LLM-based pseudo value generation
- Handles both two-column and three-column CSV formats

## Example Workflow

1. Place `.docx` files in `spool/input/`.
2. Run the extract stage to create a merged sensitive data CSV.
3. Run the generate stage to create a pseudo values CSV.
4. Run the replace stage to produce anonymized `.docx` files.

## Contributing

Feel free to submit issues or pull requests for improvements and new features.

---

**Note:**  
- Ensure your `.env` file is set up with your OpenAI API key for LLM features.
- For best results, always run scripts from the project root.