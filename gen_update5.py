import os

files = [
    'backend/schemas.py',
    'backend/routers/auth.py',
    'backend/services/ai_service.py',
    'frontend/js/api.js',
    'frontend/js/components/settings.js'
]

with open('update5.sh', 'w', encoding='utf-8', newline='\n') as out:
    for f in files:
        out.write("cat << 'EOF' > /opt/farmwatch/" + f + "\n")
        with open(f, 'r', encoding='utf-8') as inf:
            out.write(inf.read())
        if not open(f, 'r', encoding='utf-8').read().endswith('\n'):
            out.write('\n')
        out.write("EOF\n")
    out.write('cd /opt/farmwatch && docker compose build && docker compose up -d\n')
