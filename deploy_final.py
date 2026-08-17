import os
import urllib.request
import base64

files_to_update = [
    "backend/models/models.py",
    "backend/schemas.py",
    "backend/routers/farms.py",
    "backend/routers/tasks.py",
    "backend/routers/webhook.py",
    "backend/services/line_service.py",
    "frontend/js/api.js",
    "frontend/js/components/settings.js",
    "frontend/js/components/progress.js",
    "frontend/js/components/photo-wall.js",
    "backend/upgrade_db.py"
]

sh_content = "#!/bin/bash\ncd /opt/farmwatch\n"

for f in files_to_update:
    path = os.path.join(r"C:\Users\DESMOND\.gemini\antigravity\scratch\farmwatch", f.replace("/", "\\"))
    if not os.path.exists(path):
        continue
    with open(path, "rb") as file:
        content = base64.b64encode(file.read()).decode('utf-8')
    dname = os.path.dirname(f)
    if dname:
        sh_content += f"mkdir -p {dname}\n"
    sh_content += f"echo '{content}' | base64 -d > {f}\n"

sh_content += """
echo 'Restarting Docker Containers (without cache)...'
if command -v docker-compose &> /dev/null; then
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
else
    docker compose down
    docker compose build --no-cache
    docker compose up -d
fi

echo 'Update Complete! ?'
"""

with open("update.sh", "wb") as f:
    f.write(sh_content.encode('utf-8'))

# Upload to dpaste
import urllib.parse
data = urllib.parse.urlencode({'content': sh_content, 'lexer': 'bash', 'format': 'url'}).encode('utf-8')
req = urllib.request.Request("https://dpaste.com/api/v2/", data=data, method="POST")
try:
    with urllib.request.urlopen(req) as response:
        url = response.read().decode('utf-8').strip()
        print(f"URL:{url}.txt")
except Exception as e:
    print(f"Error: {e}")
