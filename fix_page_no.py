import re

fp = "1450Multiple.TulucIslam.AOCP202411031216-urd1"

with open(fp, mode="r", encoding="utf-8") as file:
    text = file.read()

def fix_number(m):
    start = m.group(1)
    page_no = int(m.group(2))
    suffix = m.group(3)
    if suffix == "A":
        new_page_number = 2 * page_no
    else:
        new_page_number = 2 * page_no + 1
    print(new_page_number)
    return f"{start}{new_page_number:03d}"

text = re.sub("(PageV\d+P)(\d+)([AB])", fix_number, text)
print(text[:5800])

fp = "1450Multiple.TulucIslam.AOCP202411031216-urd1_corrected"
with open(fp, mode="w", encoding="utf-8") as file:
    file.write(text)
