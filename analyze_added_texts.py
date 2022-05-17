import re
import os

meta_fp = r"D:\London\publications\co-authored vol\PeterChapterOnOpenITI\meta"
meta_fp = r"D:\London\OpenITI\metadata\automation\kitab-metadata-automation\kitab-metadata-automation\output"
meta_fp += r"\OpenITI_Github_clone_metadata_light.csv"


with open(meta_fp, encoding="utf-8") as file:
    meta = file.read().splitlines()
    header = meta.pop(0)

authors = set()
books = set()

for row in meta:
##    for i, c in enumerate(row.split("\t")):
##        print(i, c)
##    input("continue?")
    uri = row.split("\t")[0]
    authors.add(uri.split(".")[0])
    books.add(".".join(uri.split(".")[:2]))
##print(len(books))
##for a in books:
##    print([a])
##    input()


with open("log.md", encoding="utf-8") as file:
    log = file.read()
last = re.split("---+", log)[-1]
last = re.findall("    to (\S+)", last)
new_authors = set()
new_books = set()
new_versions = set()
collections = dict()
for fp in last:
    author = re.findall("data/([^/]+)", fp)[0]
    book = re.findall(author+"\.\w+", fp)[0]
    coll = re.findall(book+"\.(\w+\D)\d{2,}(?:BK\d)?-[a-z]{3}\d", fp)[0]
    if not coll in collections:
        collections[coll] = []
    collections[coll].append(fp)
    #print(author, book)
    if not author in authors:
        new_authors.add(author)
    if book not in books:
        new_books.add(book)


print("New text files added to corpus:", len(last))
print("Books added are from the following collections:")
for coll in collections:
    print("    {}: {} text files".format(coll, len(collections[coll])))
    if coll == "PES":
        print(collections[coll])
print("New authors:", len(new_authors))
print("New books:", len(new_books))
input()


print("List of all new authors:")
for i, a in enumerate(sorted(new_authors)):
    print(i, a)

print("List of all new books:")
for i, b in enumerate(sorted(new_books)):
    print(i, b)

print("New text files added to corpus:", len(last))
print("New authors:", len(new_authors))
print("New books:", len(new_books))
