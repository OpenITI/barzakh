"""Add OCR'ed texts to barzakh.

Provide a tsv file that contains metadata on the files
(e.g., Google sheet: https://docs.google.com/spreadsheets/d/1SxMcgHuPCrUca2V0IO2zlQrkRR28T6DwErMCAVoDzTQ/edit#gid=0)
"""

import os
import re
from shutil import copyfile
from openiti.helper.yml import readYML, dicToYML
import urllib.request

meta_fp = "meta/Corpus_Metadata_Links.tsv" # Google sheet: https://docs.google.com/spreadsheets/d/1SxMcgHuPCrUca2V0IO2zlQrkRR28T6DwErMCAVoDzTQ/edit#gid=0
ocr_folder = "D:\London\OCR\ocr_with_kraken\OUTPUT_FILES"
dest_folder = "."

def add_to_yml(yml_fp, based, link, notes, issues):
    yml = readYML(yml_fp)
    if based:
        yml["80#VERS#BASED####:"] = based
    if link:
        yml["80#VERS#LINKS####:"] = urllib.request.unquote(link)
    if notes:
        yml["90#VERS#COMMENT##:"] += "¶    NOTE: " + notes
    if yml["90#VERS#ISSUES###:"]:
        if issues:
            yml["90#VERS#ISSUES###:"] += "; UNCORRECTED_OCR; "  + issues
        else:
            yml["90#VERS#ISSUES###:"] += "; UNCORRECTED_OCR"
    else:
        yml["90#VERS#ISSUES###:"] = "UNCORRECTED_OCR"
    with open(yml_fp, mode="w", encoding="utf-8") as file:
        file.write(dicToYML(yml))
  

with open(meta_fp, mode="r", encoding="utf-8") as file:
    meta = file.read().splitlines()
    header = meta.pop(0)

for row in meta:
    row = row.split("\t")
    book_uri = row[0]
    book_folder = os.path.join(ocr_folder, book_uri)
    if os.path.exists(book_folder):
        for fn in os.listdir(book_folder):
            fp = os.path.join(book_folder, fn)
            dest_fp = os.path.join(dest_folder, fn)
            copyfile(fp, dest_fp)
            if fn.endswith(".yml"):
                add_to_yml(dest_fp, row[1], row[2], row[4], row[5])
            new_uri = row[6].strip()
            if new_uri: # replacement URI
                new_fp = re.sub(book_uri, new_uri, dest_fp)
                os.replace(dest_fp, new_fp)
                #print("renaming", dest_fp, ">", new_fp)
    else:
        print("!!", book_folder, "does not exist")

# check if more than one version is in the destination folder:
versions_d = dict()
for fn in os.listdir(dest_folder):
    if fn.endswith(".yml"):
        version_uri = fn[:-4]
        book_uri = ".".join(version_uri.split(".")[:-1])
        if not book_uri in versions_d:
            versions_d[book_uri] = []
        versions_d[book_uri].append(version_uri)

# remove all but the most recent version: 
for book_uri, version_list in versions_d.items():
    if len(version_list) > 1:
        print("  most recent version:", sorted(version_list)[-1])
        for fn in sorted(version_list)[:-1]:
            fp = os.path.join(dest_folder, fn)
            print("    removing", fp)
            print("    removing", fp+".yml")
            os.remove(fp)
            os.remove(fp+".yml")
        
