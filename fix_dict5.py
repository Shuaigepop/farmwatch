import os
import re

filepath = 'frontend/js/components/settings.js'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace with wildcards for the mojibake parts
replacements = [
    (r'LINE 群组.*?系统将自动绑定讯.*?。', 'LINE 群组如果与此处设定的农场名称完全相同，系统将自动绑定讯息。'),
    (r'使用者管.*? \(User', '使用者管理 (User'),
    (r'管.*?已.*?加入.*? LINE 群组.*?农场.*?连结.*?连结.*?机器人.*?自动推播通知。', '管理已加入的 LINE 群组与农场的连结，重新连结后机器人会自动推播通知。'),
    (r'区域管.*? \(Zone', '区域管理 (Zone'),
    (r'管.*?农场.*?区域 \(例如: A.*?A1等\)', '管理农场底下的区域 (例如: A区、A1等)'),
    (r'没有任何农场。', '目前没有任何农场。'),
    (r'没有任何使用者。', '目前没有任何使用者。'),
    (r'>.*?登入.*?<', '>登入帐号<'),
    (r'新密码 \(.*?空.*?改\)', '新密码 (留空不改)'),
    (r'没有.*?加入任何 LINE 群组。', '目前没有加入任何 LINE 群组。'),
    (r'连结更新.*?机器人已.*?通知', '连结更新成功，机器人已发通知'),
    (r'选.*?农场以管.*?区域\.\.\.', '选择农场以管理区域...'),
    (r'该农场.*?没有设定任何区域。', '该农场目前没有设定任何区域。')
]

for pat, repl in replacements:
    text = re.sub(pat, repl, text, flags=re.DOTALL)

# Clean up any remaining typical mojibake characters manually
text = text.replace('ç›®å‰ ', '目前')
text = text.replace('ç™»å…¥å¸ å ·', '登入帐号')
text = text.replace('ã€‚', '。')
text = text.replace('ï¼Œ', '，')
text = text.replace('çš„', '的')
text = text.replace('ä¸Ž', '与')
text = text.replace('å¦‚æžœ', '如果')
text = text.replace('æˆ åŠŸ', '成功')

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
