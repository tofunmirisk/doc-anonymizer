import re

ANCHORS = ['INSURED', 'REINSURED', 'REINSURER', 'BROKER', 'COMPANY']

def extract_company_names(lines):
    full_text = "\n".join(lines)
    company_blocks = []
    
    i = 0
    while i < len(lines):
        line_upper = lines[i].upper()
        if any(anchor in line_upper for anchor in ANCHORS):
            buffer = []
            i += 1
            # Capture up to 3 lines or until stop condition
            while i < len(lines) and len(buffer) < 3:
                current = lines[i]
                if re.match(r'^[A-Z\s\-]+:$', current):  # next section header
                    break
                buffer.append(current)
                i += 1
            if buffer:
                company_blocks.append("\n".join(buffer))
        else:
            i += 1
    
    # Also use spaCy + regex fallback for one-liners
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        spacy_doc = nlp(full_text)
        orgs = {ent.text.strip() for ent in spacy_doc.ents if ent.label_ == "ORG"}
    except:
        orgs = set()

    # Regex suffix fallback
    suffix_pattern = r"\b[A-Z][\w&\-,\.\s]+?\b(?:Ltd|Limited|Inc|LLP|Plc|SE|AG|GmbH|S\.A\.)\b"
    suffix_matches = set(re.findall(suffix_pattern, full_text))

    # Union of all
    all_orgs = set(company_blocks).union(orgs).union(suffix_matches)
    print(all_orgs)

    # Use LLM to filter and clean up the company names
    from utils.extract_utils import llm_filter
    text= "\n".join(all_orgs)
    prompt = f"""Extract all company names from the text. 
    Return them exactly as they appear, preserving multi-line names and context. 
    Do not remove any words that might also function as part of other text.
    Do not enumerate or hyphenate or number the results.
    Return value as next line separated values, one company name per line.:
    \n{text}
    """
    filtered_orgs = llm_filter(prompt,
                system_role="You are an expert in extracting company names from text.",
                model="gpt-4o"
    )

    return sorted(filtered_orgs)
