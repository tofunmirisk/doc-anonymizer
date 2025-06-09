def extract_addresses(texts):
    """
    Extract addresses from a list of text strings.
    :param texts: List of strings (paragraphs, table cells, etc.)
    :return: Set of addresses found
    """
    # TODO: Implement extraction logic
    return set()

# address_extractor.py

import re

ADDRESS_ANCHORS = ['address', 'registered office', 'head office', 'location', 'principal place']
UK_POSTCODE_PATTERN = r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b"
ADDRESS_LINE_PATTERN = r"(.{5,}),\s+([A-Za-z\s]+)(,\s+[A-ZaLettters\s]+)*"  # e.g., Street, City, Country

def extract_addresses(lines):
    full_text = "\n".join(lines)
    addresses = set()

    # Anchor-based multiline
    for i, line in enumerate(lines):
        if any(anchor in line.lower() for anchor in ADDRESS_ANCHORS):
            buffer = []
            j = i + 1
            while j < len(lines) and len(buffer) < 4:
                buffer.append(lines[j])
                if re.search(UK_POSTCODE_PATTERN, lines[j]):
                    break
                j += 1
            if buffer:
                addresses.add("\n".join(buffer))

    # Inline address pattern (comma-separated lines with place names)
    for line in lines:
        if re.search(ADDRESS_LINE_PATTERN, line):
            addresses.add(line)
    
    # Fallback for multi-line addresses, breakout into independent lines
    for line in lines:
        if re.search(r"\b\d{1,5}\s+\w+(\s+\w+)*,\s+\w+(\s+\w+)*,\s+\w+(\s+\w+)*", line):
            addresses.add(line.strip())

    # UK postcode-based backtracking
    for i, line in enumerate(lines):
        if re.search(UK_POSTCODE_PATTERN, line):
            block = lines[max(0, i-2):i+1]
            addresses.add("\n".join(block))

    # Named entity recognition (optional)
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc_spacy = nlp(full_text)
        for ent in doc_spacy.ents:
            if ent.label_ in ["GPE", "LOC"]:
                phrase = ent.text.strip()
                if "," in phrase or len(phrase.split()) > 1:
                    addresses.add(phrase)
    except:
        pass

    # Further separate addresses by comma and add as new entries
    separated_addresses = set()
    for addr in addresses:
        if "," in addr:
            parts = [part.strip() for part in addr.split(",") if part.strip()]
            separated_addresses.update(parts)
        else:
            separated_addresses.add(addr)
    addresses = separated_addresses

    print("\n".join(addresses))

    # Use LLM to filter and clean up the addresses
    from utils.extract_utils import llm_filter
    text = "\n".join(addresses)
    prompt = f"""Extract all addresses from the text. 
    Return each address exactly as it appears, as a separate line. 
    Use preceding text as context consider current line as an address. 
    Don't merge address lines into a single address if they are within the same context
    Do not enumerate, hyphenate, or number the results.:
    \n{text}
    """
    filtered_addrs = llm_filter(
        prompt,
        system_role="You are an expert in extracting addresses from text.",
        model="gpt-4o"
    )

    return sorted(filtered_addrs)
