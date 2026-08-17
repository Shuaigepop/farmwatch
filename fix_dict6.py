import os
import re

filepath = 'frontend/js/components/settings.js'
with open(filepath, 'r', encoding='utf-8') as f:
    text = f.read()

replacements = [
    (r'ç¡®å®šè¦ åˆ.é™¤æ.¤åŒºåŸŸå —ï¼Ÿ', '确定要删除此区域吗？'),
    (r'ç¡®å®šè¦ åˆ.é™¤è¿™ä¸ªå†œåœºå —ï¼Ÿæ.¤æ“ ä½œæ—.æ³.æ’¤é”€ã€‚', '确定要删除这个农场吗？此操作无法撤销。'),
    (r'ç¡®å®šè¦ åˆ.é™¤ä½¿ç”¨è€…ã€Œ', '确定要删除使用者「'),
    (r'ã€ å —ï¼Ÿæ.¤æ“ ä½œæ—.æ³.æ’¤é”€ã€‚', '」吗？此操作无法撤销。'),
    (r'å»ºç«‹中 \(Creating\)\.\.\.', '建立中 (Creating)...'),
    (r'å»ºç«‹失败', '建立失败'),
    (r'å†œåœºå»ºç«‹æˆ åŠŸ！', '农场建立成功！'),
    (r'删除失败', '删除失败'),
    (r'新增成功', '新增成功')
]

for pat, repl in replacements:
    text = re.sub(pat, repl, text, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
