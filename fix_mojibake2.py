import os
import re

filepath = 'frontend/js/components/settings.js'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

def fix_mojibake(match):
    s = match.group(0)
    try:
        # Encode to cp1252, decode to utf-8
        decoded = s.encode('cp1252').decode('utf-8')
        # Only replace if the result contains CJK characters
        if any('\u4e00' <= c <= '\u9fff' for c in decoded):
            return decoded
    except:
        pass
    return s

# Match sequences of characters that are typically cp1252 mojibake for UTF-8 Chinese
# This includes characters like ç (e7), æ (e6), å (e5), etc.
# Actually, we can just match any non-ASCII characters and try to decode them
fixed_text = re.sub(r'[^\x00-\x7F]+', fix_mojibake, text)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(fixed_text)
print("Finished mojibake decoding.")
