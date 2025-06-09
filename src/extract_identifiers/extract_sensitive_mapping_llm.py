import openai

def extract_sensitive_mapping_llm(text, openai_api_key, model="gpt-4o"):
    """
    Use an LLM to extract a mapping of all sensitive/identifying values for simple search and replace.
    Returns a dict: {original_value: [variant1, variant2, ...]}
    """
    prompt = f"""
You are an expert in document anonymization.

Given the following contract content, extract all sensitive or identifying values for simple search and replace.
- Ensure all mappings are exact string matches for straightforward replacement.
- Include multiple variants for each identified value across different formats in the document.
- For each original identifying value (company names, brokers, UMRs, addresses, clause references, monetary values, etc.):
    - Include the exact match as it appears.
    - If the identifier spans multiple lines, treat each line and the full span as a distinct replacement.
    - Maintain all punctuation and spacing.
    - Include formatted or abbreviated forms if they appear (e.g., L.P., LP, with/without commas).

### 🔐 ENTITIES TO REPLACE
- Company names
- Brokers
- UMRs or policy references
- Addresses
- Market references
- Insurers
- Policy wording clause references
- Financial values (premiums, taxation, limits)

### 📄 USAGE CONTEXT
This mapping will be used for direct string replacement using .replace() or similar functions without regex, so context integrity must be preserved.

Return your answer as a valid Python dictionary in the format:
{{"original_value1": ["variant1", "variant2"], "original_value2": ["variant1"], ...}}

--- CONTRACT CONTENT START ---
{text}
--- CONTRACT CONTENT END ---
"""

    openai.api_key = openai_api_key
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant for extracting sensitive values for anonymization."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2048,
        temperature=0
    )
    import ast
    try:
        mapping = ast.literal_eval(response['choices'][0]['message']['content'])
        return mapping
    except Exception:
        # Fallback: return raw string if parsing fails
        return response['choices'][0]['message']['content'].strip()