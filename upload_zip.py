import os
import zipfile
import urllib.request
import json
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

zip_path = "farmwatch_update.zip"
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for folder in ['backend', 'frontend']:
        folder_path = os.path.join(r"C:\Users\DESMOND\.gemini\antigravity\scratch\farmwatch", folder)
        for root, dirs, files in os.walk(folder_path):
            if '__pycache__' in root:
                continue
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, r"C:\Users\DESMOND\.gemini\antigravity\scratch\farmwatch")
                zipf.write(file_path, arcname)

# Create a setup.sh script to run after unzip
setup_script = """#!/bin/bash
cd /opt/farmwatch
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
echo 'Update Complete! ✨'
"""
with zipfile.ZipFile(zip_path, 'a') as zipf:
    zipf.writestr('setup.sh', setup_script)

print("Zip created. Uploading to file.io...")

# Upload to file.io
with open(zip_path, 'rb') as f:
    req = urllib.request.Request("https://file.io/?expires=1w", data=f, method="POST")
    req.add_header('Content-Type', 'application/zip')
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            print("URL: " + res_data['link'])
    except Exception as e:
        print(f"Error: {e}")
