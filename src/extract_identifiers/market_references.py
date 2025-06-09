import re

PATTERNS = {
    "UMR": r"\bB\d{4}[A-Z]{0,2}\d{6,10}\b",                    # B0507LF2301988
    "LIRMA": r"\bU\d{7}[A-Z]?\b",                              # U1234567A
    "BINDER": r"\bY\d{9}[A-Z]?\b",                             # Y123456789L
    "POLICY_ID": r"\b[A-Z]?\d{5,7}/\d{2,4}\b",                 # P123456/2023
    "SLIP_LEADER": r"\bSL\d{6,10}\b",                          # SL12345678
    "ENDORSEMENT": r"\bEND/\d{4}/\d{3,6}\b",                   # END/2023/0045
    "REFERENCE": r"\bREF-[A-Z]{2,3}-\d{4,5}-\d{4}\b",          # REF-UK-00567-2023
    "QUOTE": r"\b(QRT|QUO)\d{6,8}[A-Z]{0,4}\b",                # QRT20230615XYZ
    "RISK_REF": r"\bRRX\d{6,10}\b",                            # RRX987654321
    "LCN": r"\bLCN\d{6,10}\b",                                 # LCN12345678
    "TRIA": r"\bTRIA-\d{9,12}\b",                               # TRIA-123456789
    "GENERIC_ID": r"\b(?=[A-Za-z]*\d)(?=\d*[A-Za-z])[A-Za-z0-9\-_\/]{6,30}\b"
}

def extract_market_references(lines):
    full_text = "\n".join(lines)

    references = set()
    for pattern in PATTERNS.values():
        matches = re.findall(pattern, full_text)
        for match in matches:
            references.add(match)
    
    return sorted(references)
