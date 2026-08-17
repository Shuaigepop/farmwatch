import re

def fix_settings():
    with open('frontend/js/components/settings.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # The mojibake is valid UTF-8 that was mistakenly interpreted as latin-1 or cp1252.
    # To fix it, we need to extract the mojibake, encode to latin-1, and decode to utf-8.
    
    # We will find all chunks of characters that are either in 0x80-0xFF, or are punctuation
    # sometimes mixed in. However, since the only non-ASCII characters in this file that are valid
    # are the ones we added or are in the correct Chinese text, we can use a trick:
    # ANY character > 127 in the file that was part of the mojibake will be converted.
    # Wait, there are valid Chinese characters in the file like "新增农场 (Create New Farm)".
    # If we encode them to latin-1, it raises ValueError.
    
    def replacer(match):
        text = match.group(0)
        try:
            return text.encode('latin-1').decode('utf-8')
        except:
            return text

    # We match consecutive characters that are >= 128 (0x80)
    # This will match the mojibake. But wait, we already tried this and it failed.
    # Why? Because some characters in the mojibake might be < 128 if CP1252 mapped some bytes
    # to characters < 128? NO, CP1252 bytes 0x80-0xFF all map to characters >= 0x80 EXCEPT:
    # 0x80 -> \u20ac, 0x82 -> \u201a, 0x83 -> \u0192, 0x84 -> \u201e, 0x85 -> \u2026, 0x86 -> \u2020, 0x87 -> \u2021, 0x88 -> \u02c6, 0x89 -> \u2030, 0x8a -> \u0160, 0x8b -> \u2039, 0x8c -> \u0152, 0x8e -> \u017d, 0x91 -> \u2018, 0x92 -> \u2019, 0x93 -> \u201c, 0x94 -> \u201d, 0x95 -> \u2022, 0x96 -> \u2013, 0x97 -> \u2014, 0x98 -> \u02dc, 0x99 -> \u2122, 0x9a -> \u0161, 0x9b -> \u203a, 0x9c -> \u0153, 0x9e -> \u017e, 0x9f -> \u0178.
    # Wait! CP1252 maps some bytes to Unicode characters > 255 (like \u20ac).
    # IF the file was decoded as CP1252 instead of latin-1, then `text.encode('latin-1')` will FAIL!
    # YES! This is exactly why it failed!
    
    def cp1252_replacer(match):
        text = match.group(0)
        try:
            return text.encode('cp1252').decode('utf-8')
        except:
            return text

    # We need to match ANY character that is not standard ASCII (ord >= 128)
    # plus any ASCII characters that might be part of it (but actually UTF-8 bytes > 127 map to CP1252 chars > 127).
    content = re.sub(r'[^\x00-\x7F]+', cp1252_replacer, content)

    with open('frontend/js/components/settings.js', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    fix_settings()
