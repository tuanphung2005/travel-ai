import os
import re
import json

def decode_match(match):
    s = match.group(0)
    # the regex matched things like \ud83c\udf3f
    # json.loads('"\ud83c\udf3f"') correctly interprets surrogate pairs
    try:
        return json.loads('"' + s + '"')
    except Exception as e:
        return s

target_dir = r'c:\Users\bring\coding\travel-ai\app\templates'
for f in os.listdir(target_dir):
    if f.startswith('debug_') and f.endswith('.py'):
        path = os.path.join(target_dir, f)
        with open(path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        new_content = re.sub(r'(?:\\u[0-9a-fA-F]{4})+', decode_match, content)
        new_content = re.sub(r'(?:\\\\u[0-9a-fA-F]{4})+', lambda m: decode_match(re.match(r'(?:\\\\u([0-9a-fA-F]{4}))+', m.group(0)).group(0).replace(r'\\', '\\')), new_content)

        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print("Fixed", f)
