import re

with open('frontend/js/app.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace any ?v=number with ?v=9 in imports
text = re.sub(r'(from\s+[\'"].*?\.js)(\?v=\d+)?([\'"])', r'\g<1>?v=9\g<3>', text)

with open('frontend/js/app.js', 'w', encoding='utf-8') as f:
    f.write(text)

with open('frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'(src=["\'].*?\.js)(\?v=\d+)?(["\'])', r'\g<1>?v=9\g<3>', text)

with open('frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Added cache-busting strings to imports.')
