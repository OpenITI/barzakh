import re

fn = "0805CabdKarimJili.IsfarCanAnwar.IAC00036-ara1"
with open(fn, encoding="utf8") as file:
    text = file.read()

matn = """#####OpenITI#

#META# title: رسالة الأنوار
#META# author: محي الدين ابن العربي
#META# source: https://ibnalarabi.com/jili/isfar.php

#META#Header#End#

"""

sharh = """#####OpenITI#

#META# title: الأسفار عن رسالة الأنوار فيما يتجلى لأهل الذكر من الأنوار
#META# author: عبد الكريم بن إبراهيم الجيلي
#META# source: https://ibnalarabi.com/jili/isfar.php

#META#Header#End#

"""


text = re.split("#META#Header#End#", text, maxsplit=1)[-1]
text = re.sub(r"\r", "", text)

sharh_splitter = r"# (?:[.…-] *){10,}\.?(?:\n~~(?:[.…-] *)+\.?)?"


m = None
s = None
page_no = None
for page in re.split(r"(PageV\d+P\d+)", text):
    #print(page)
    if page.startswith("Page"):
        page_no = page
        if m.strip():
            matn += f"\n{m.strip()}\n{page_no}"
        sharh += f"\n{s.strip()}\n{page_no}"
    else:
        if not page.strip():
            m = ""
            s = ""
            continue
        try:
            m, s = re.split(sharh_splitter, page)
        except:
            print("no splitter on page", page_no)
            #r = input("print page? y/N: ")
            #if r.lower() == "y":
            #    print(re.split(sharh_splitter, page))
            #print(page_no)
            #print("-----")
            m = ""
            s = page

matn_fn = "0638IbnCarabi.Anwar.IAC00036BK1-ara1"
sharh_fn = "0805CabdKarimJili.IsfarCanAnwar.IAC00036BK2-ara1"
with open(matn_fn, mode="w", encoding="utf-8") as file:
    file.write(matn)
with open(sharh_fn, mode="w", encoding="utf-8") as file:
    file.write(sharh)


            

