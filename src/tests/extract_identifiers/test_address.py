# test_address_extractor.py

from extract_identifiers.addresses import extract_addresses
from extract_identifiers.utils import create_docx
import os


def test_postcode_based_address():
    create_docx([
        "Registered Office:",
        "Sanctuary House",
        "5 Old Broad Street",
        "London",
        "EC2N 1DW"
    ], "test_postcode_address.docx")

    expected = "Sanctuary House\n5 Old Broad Street\nLondon\nEC2N 1DW"
    addresses = extract_addresses("test_postcode_address.docx")
    os.remove("test_postcode_address.docx")

    assert expected in addresses, "❌ Address block with postcode not detected."
    print("✅ Postcode-based address extraction passed.")

def test_standalone_postcode_heuristic():
    create_docx([
        "NovaSecure Risk Ltd",
        "Flat 8, Keats House",
        "W1A 1AA"
    ], "test_standalone.docx")

    expected = "NovaSecure Risk Ltd\nFlat 8, Keats House\nW1A 1AA"
    addresses = extract_addresses("test_standalone.docx")
    os.remove("test_standalone.docx")

    assert expected in addresses, "❌ Heuristic postcode block not detected."
    print("✅ Standalone postcode heuristic extraction passed.")

def test_multiple_addresses():
    create_docx([
        "Location:",
        "1 Leadenhall Street",
        "London",
        "EC3V 1PP",
        "Head Office:",
        "100 Bishopsgate",
        "London",
        "EC2N 4AG"
    ], "test_multiple.docx")

    addresses = extract_addresses("test_multiple.docx")
    os.remove("test_multiple.docx")

    expected_1 = "1 Leadenhall Street\nLondon\nEC3V 1PP"
    expected_2 = "100 Bishopsgate\nLondon\nEC2N 4AG"

    assert any(expected_1 in addr for addr in addresses)
    assert any(expected_2 in addr for addr in addresses)
    print("✅ Multiple address block extraction passed.")

if __name__ == "__main__":
    test_postcode_based_address()
    test_standalone_postcode_heuristic()
    test_multiple_addresses()
