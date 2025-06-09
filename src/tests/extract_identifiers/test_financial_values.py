from extract_identifiers.financial_values import extract_financial_values
from extract_identifiers.utils import create_docx
import os

def test_spacy_and_regex_blend():
    create_docx([
        "Limit: GBP 5,000,000",
        "Deductible: £1,000.00",
        "Insured for one million pounds.",
        "Tax paid: USD 50,000.50",
        "Excess: ₦2,500,000",
        "Total Premium is five hundred thousand naira only"
    ], "test_financial_blend.docx")

    values = extract_financial_values("test_financial_blend.docx")
    os.remove("test_financial_blend.docx")

    expected_substrings = [
        "GBP 5,000,000",
        "£1,000.00",
        "one million pounds",
        "USD 50,000.50",
        "₦2,500,000",
        "five hundred thousand naira"
    ]

    for val in expected_substrings:
        assert any(val.lower() in v.lower() for v in values), f"❌ Missing or misdetected: {val}"

    print("✅ spaCy + regex financial value extraction passed.")
