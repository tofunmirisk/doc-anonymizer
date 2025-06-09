import re
from docx import Document

# Improved pattern: avoid matching dates, standalone years, and capture % values
CURRENCY_PATTERN = re.compile(
    r"""
    (?<!\d[\/\.])                # Not preceded by digit + / or .
    (?:GBP|USD|EUR|£|\$)?\s?     # Optional currency symbol/code
    [\d,]+(?:\.\d{1,2})?         # Digits with optional decimal
    (?![\/\.]\d{1,4})            # Not followed by / or . and more digits (date)
    \s?(?:USD|GBP|EUR)?          # Optional trailing currency code
    """,
    re.IGNORECASE | re.VERBOSE
)

PERCENT_PATTERN = re.compile(
    r"\b\d{1,3}(?:\.\d+)?\s?%", re.IGNORECASE
)

def looks_like_date_or_year(s):
    s = s.strip()
    # Matches dates like 12/12/2024, 12.12.2024, 2024-12-12, etc.
    if re.match(r"\d{1,2}[\/\.-]\d{1,2}[\/\.-]\d{2,4}", s):
        return True
    # Matches only a year (1900-2099)
    if re.match(r"^(19|20)\d{2}$", s):
        return True
    return False

def is_short_number(s):
    # Remove commas, currency, percent, and spaces, then check digit length
    s_clean = re.sub(r"[^\d]", "", s)
    return len(s_clean) <= 2

def extract_financial_values(lines, use_spacy=True):
    """
    Extract financial values (premiums, limits, taxation, percentages) from a DOCX file.
    :param lines: List of text lines
    :param use_spacy: Whether to use spaCy for NER
    :return: Set of financial values found
    """
    full_text = "\n".join(lines)
    results = set()

    # Regex extraction (avoid dates and years, remove short numbers)
    regex_matches = [m.group().strip() for m in CURRENCY_PATTERN.finditer(full_text) if m.group().strip()]
    for match in regex_matches:
        if not looks_like_date_or_year(match) and not is_short_number(match):
            results.add(match)

    # Capture numbers preceding %
    percent_matches = [m.group().strip() for m in PERCENT_PATTERN.finditer(full_text) if m.group().strip()]
    for match in percent_matches:
        if not is_short_number(match):
            results.add(match)

    # spaCy-based extraction (NER for MONEY)
    if use_spacy:
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            doc_spacy = nlp(full_text)
            for ent in doc_spacy.ents:
                if ent.label_ == "MONEY":
                    if not looks_like_date_or_year(ent.text) and not is_short_number(ent.text):
                        results.add(ent.text.strip())
        except Exception as e:
            print(f"[spaCy fallback]: {e}")

    return sorted(results)
