import urllib.request
import urllib.parse
import sys

try:
    with open('update.sh', 'r', encoding='utf-8') as f:
        content = f.read()

    data = urllib.parse.urlencode({'content': content, 'lexer': 'bash', 'format': 'url'}).encode('utf-8')
    req = urllib.request.Request("https://dpaste.com/api/v2/", data=data, method="POST")
    with urllib.request.urlopen(req) as response:
        url = response.read().decode('utf-8').strip()
        print(f"URL:{url}.txt")
except Exception as e:
    print(f"Error: {e}")
