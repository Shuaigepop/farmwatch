import os

def unescape_backticks(filepath):
    if not os.path.exists(filepath):
        print(f"File {filepath} not found.")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace \` with `
    if r'\`' in content:
        print(f"Fixing {filepath}")
        content = content.replace(r'\`', '`')
        
        # Also replace \${} with ${} if they were escaped
        content = content.replace(r'\${', '${')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        print(f"No escaped backticks in {filepath}")

unescape_backticks('frontend/js/inventory.js')
unescape_backticks('frontend/js/reports.js')
unescape_backticks('frontend/js/components/inventory.js')
unescape_backticks('frontend/js/components/reports.js')
