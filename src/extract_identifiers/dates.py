# date_extractor.py

import re
from docx import Document

DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # 01/01/2024
    r"\b\d{4}-\d{2}-\d{2}\b",              # 2024-01-01
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)[,]?\s+\d{4}\b",
    r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?[,]?\s+\d{4}\b",
    r"\bthe\s+\d{1,2}(?:st|nd|rd|th)?\s+of\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b"
]

def extract_dates(lines):
    results = set()
    full_text = "\n".join(lines)
    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, full_text)
        if not matches:
            continue
        # If the first match is a tuple, flatten all matches
        if isinstance(matches[0], tuple):
            for m in matches:
                results.add("".join(m))
        else:
            for m in matches:
                results.add(m)
    return sorted(results)
