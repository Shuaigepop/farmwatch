import os

filepath = 'frontend/js/components/settings.js'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

try:
    # Try to reverse the mojibake by encoding back to cp1252 (or latin1) and decoding as utf-8
    fixed_text = text.encode('cp1252').decode('utf-8')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_text)
    print("Successfully decoded mojibake using cp1252.")
except Exception as e:
    print(f"Failed to decode using cp1252: {e}")
    try:
        fixed_text = text.encode('latin1').decode('utf-8')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_text)
        print("Successfully decoded mojibake using latin1.")
    except Exception as e2:
        print(f"Failed to decode using latin1: {e2}")

