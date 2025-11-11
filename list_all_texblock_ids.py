import os
import re

base_folder = "eScriptorium_alto"
ids = set()
for root, dirs, files in os.walk(base_folder):
    for fn in files:
        if fn.endswith("xml"):
            with open(os.path.join(root, fn), encoding="utf-8") as file:
                text = file.read()
                ptrn = 'TextBlock ID="[^"]+"'
                for block_id in re.findall(ptrn, text):
                    ids.add(block_id)

for textblock_id in set(ids):
    print(textblock_id)
                
                
    
