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
    "backend/upgrade_db.py",
    "backend/setup_rich_menu.py"
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
echo 'Running DB Upgrade...'
cd backend
python3 upgrade_db.py
cd ..
echo 'Restarting Docker Containers...'
docker-compose down
docker-compose up -d --build
echo 'Deploying Rich Menu...'
cd backend
python3 setup_rich_menu.py
cd ..
echo 'Update Complete!'
"""

with open("update.sh", "wb") as f:
    f.write(sh_content.encode('utf-8'))

req = urllib.request.Request("https://0x0.st", data=b"file=" + urllib.parse.quote(sh_content).encode('utf-8'), method="POST")
try:
    with urllib.request.urlopen(req) as response:
        paste_url = response.read().decode('utf-8').strip()
        print(f"URL:{paste_url}")
except Exception as e:
    print(f"Error 0x0: {e}")
    # Fallback to clbin
    try:
        req = urllib.request.Request("https://clbin.com", data=b"clbin=" + urllib.parse.quote(sh_content).encode('utf-8'), method="POST")
        with urllib.request.urlopen(req) as response:
            paste_url = response.read().decode('utf-8').strip()
            print(f"URL:{paste_url}")
    except Exception as e2:
        print(f"Error clbin: {e2}")

