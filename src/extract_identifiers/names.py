# name_extractor.py

import re

TITLES = ["Mr.", "Mrs.", "Ms.", "Miss", "Dr.", "Prof."]
NAME_LABELS = ["Signed by", "Underwriter", "Broker", "Prepared by", "Represented by", "For and on behalf of"]

def extract_names(lines):
    """
    Extract names from a DOCX file using title-based and label-based patterns,
    as well as spaCy's NER capabilities.
    """
    full_text = "\n".join(lines)
    names = set()

    # Pattern-based extraction (title or labels)
    title_pattern = re.compile(rf"\b({'|'.join(TITLES)})\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b")
    label_pattern = re.compile(rf"({'|'.join(NAME_LABELS)}):?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)")

    for line in lines:
        print(f"Extracting names from line: {line}")

        # Match title-based names
        for match in title_pattern.findall(line):
            split_line = line.split(match[0], 1)
            if len(split_line) > 1:
                after_title = split_line[1].strip().split()
                if after_title:
                    names.add(match[0] + " " + after_title[0])

        # Match label-based names
        for match in label_pattern.findall(line):
            names.add(match[1])

    # spaCy NER (PERSON)
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        spacy_doc = nlp(full_text)
        for ent in spacy_doc.ents:
            if ent.label_ == "PERSON":
                names.add(ent.text.strip())
    except:
        pass

    print(f"Extracted names: {names}")

    # Use LLM to filter and clean up the company names
    from utils.extract_utils import llm_filter
    text= "\n".join(names)
    prompt = f"""Extract all person names from the text. 
    Return them exactly as they appear, preserving multi-line names and context. 
    Do not enumerate or hyphenate or number the results.
    Return value as next line separated values, one name per line.:
    \n{text}
    """
    filtered_names = llm_filter(prompt,
                system_role="You are an expert in extracting person names from text.",
                model="gpt-4o"
    )

    return sorted(filtered_names)
