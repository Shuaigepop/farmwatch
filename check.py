import glob
files = glob.glob('frontend/js/**/*.js', recursive=True)
for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        if '\\`' in content:
            print(f'Found escaped backtick in {f}')
