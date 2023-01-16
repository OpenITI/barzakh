"""
Unzip the OpenITI AOCP zip files

Each zip file in turn contains two zip files: 
one containing the teixml export from eScriptorium, 
the other containing the openitimarkdown export.

The `main()` function unzips this zip file
and merges all OpenITI mARkdown page transcriptions
into one single OpenITI mARkdown text file.

"""

import os
import re
import shutil
import zipfile

from openiti.helper.funcs import natural_sort

yml_template = """\
00#VERS#LENGTH###:
00#VERS#CLENGTH##:
00#VERS#URI######: {}
80#VERS#BASED####: permalink, permalink, permalink
80#VERS#COLLATED#: permalink, permalink, permalink
80#VERS#LINKS####: permalink, permalink, permalink
90#VERS#ANNOTATOR: the name of the annotator (latin characters; please
    use consistently)
90#VERS#COMMENT##: This text was OCR'ed as part of the first phase of the OpenITI AOCP project, 
    generously funded by the Andrew W. Mellon Foundation.
    This file was created on {} 
    by eScriptorium version {}.
90#VERS#DATE#####: YYYY-MM-DD
90#VERS#ISSUES###: UNCORRECTED_OCR
"""


def merge_md(zip_fp, uri_folder):
    """Merge all page transcription OpenITI mARkdown files into a single mARkdown file
    
    Args:
        zip_fp (str): path to the zip file containing all page transcriptions
        uri_folder (str): path to the destination folder (named after the text's version URI)

    Returns:
        None
    """
    # unzip the zip file:
    folder = unzip_text_folder(zip_fp, uri_folder, file_type="md")

    # merge all separate markdown files (one file per page):
    full_text = ""
    for fn in natural_sort(os.listdir(folder)):
        if not fn.endswith(".mARkdown"):
            continue
        #print(fn)

        # read the text file
        fp = os.path.join(folder, fn)
        with open(fp, mode="r", encoding="utf-8") as file:
            page_text = file.read()
        
        # extract the page number from the filename:
        page_no = re.findall("\d+", fn)[-1]
        page_no = "\nPageV00P{:03d}\n".format(int(page_no)) 

        # remove the metadata header from the text:
        header, splitter, page_text = re.split("(#META#Header#End#[\r\n]+)", page_text, maxsplit=1)

        # extract the source image filename from the filename:
        img_fn = re.findall("#META# IMAGE FILENAME: (.+)", header)[0]
        img_link = "\n![page image](img/{})\n\n".format(img_fn)

        # add the page text to the full_text:
        full_text += img_link + page_text + page_no

    # extract the page-specific sections from the header:
    header = re.sub("#META# IMAGE.+[\r\n]+", "", header)
    header += splitter
    
    # add the metadata header to the text
    full_text = header + full_text

    # stor the text file with temporary ".txt" extension 
    # (in order not to overwrite the original folder):
    outfp = uri_folder+".txt"
    with open(outfp, mode="w", encoding="utf-8") as file:
        file.write(full_text)

    # Create the yml file:
    yml_fp = uri_folder+".yml"
    with open(yml_fp, mode="w", encoding="utf-8") as file:
        uri = os.path.basename(uri_folder)
        created_date = re.findall("CREATED: (.+)", header)[0]
        created_by = re.findall("CREATED BY: (.+)", header)[0]
        file.write(yml_template.format(uri, created_date, created_by))



def merge_tei(zip_fp, uri_folder):
    """Merge all page transcription TEI XML files into a single TEI XML file
    
    Args:
        zip_fp (str): path to the zip file containing all page transcriptions
        uri_folder (str): path to the destination folder (named after the text's version URI)

    Returns:
        None
    """

    # unzip the zip file:
    folder = unzip_text_folder(zip_fp, uri_folder, file_type="tei")
    print("write code to unzip tei xml zips")

    # merge all separate tei xml files (one file per page):
    full_text = ""
    for fn in natural_sort(os.listdir(folder)):
        if not fn.endswith(".xml"):
            continue
        print(fn)

        # read the text file
        fp = os.path.join(folder, fn)
        with open(fp, mode="r", encoding="utf-8") as file:
            page_text = file.read()
        
        # extract the page number from the filename:
        page_no = re.findall("\d+", fn)[-1]
        page_no = '\n          <pb n="{}"/>\n'.format(page_no)


        # remove the metadata header from the text:
        split_regex = "(<body>[\r\n ]+<div>[\r\n ]+<p> *)"
        header, splitter, page_text = re.split(split_regex, page_text, maxsplit=1)

        # strip off the closing p, div, TEI, body and text tags:
        footer_regex = " *</p>\n[\r\n ]+</div>[\r\n ]+</body>[\r\n ]+</text>[\r\n ]+</TEI>[\r\n ]*"
        footer = re.findall(footer_regex, page_text)[0]
        page_text = page_text[:-len(footer)]

        # extract the source image filename from the filename:
        img_fn = re.findall("IMAGE FILENAME: (.+)", header)[0]
        img_width = re.findall("IMAGE WIDTH: (.+)", header)[0]
        img_height = re.findall("IMAGE HEIGHT: (.+)", header)[0]
        img_link = '\n          <graphic url="{}" width={} height={} />\n'.format(img_fn, img_width, img_height)

        # add the page text to the full_text:
        full_text += page_no + img_link + page_text

    # remove the page-specific sections from the header:
    header = re.sub("IMAGE.+[\r\n]+", "", header)
    header += splitter
    
    # add the metadata header to the text
    full_text = header + full_text + footer

    # store the xml file: 
    outfp = uri_folder+".xml"
    with open(outfp, mode="w", encoding="utf-8") as file:
        file.write(full_text)


def unzip_text_folder(fp, uri_folder, file_type="tei"):
    """Unzip the folder containing the page transcriptions
    
    The folder will get the name of the file type ("tei", "md")
    
    Args:
        fp (str): path to the zip file
        uri_folder (str): path to the parent folder of the output folder
        file_type (str): file type of the transcription files ("tei", "md")

    Returns:
        str
    """
    dest_folder = os.path.join(uri_folder, file_type)
    if not os.path.exists(dest_folder):
        os.mkdir(dest_folder)
    with zipfile.ZipFile(fp, mode="r") as archive:
        archive.extractall(path=dest_folder)
    return dest_folder


def unzip_container(fp):
    """Unzip the main zip file to a folder with the URI as name
    
    Returns:
        str
    """
    uri_folder = fp[:-4]
    if os.path.exists(uri_folder):
        os.remove(uri_folder)
    with zipfile.ZipFile(fp, mode="r") as archive:
        #for fn in archive.namelist():
        #    print(fn)
        archive.extractall(path=uri_folder)
        #os.remove(fp)
    return uri_folder


def main(zip_fp, delete_zip=False):
    """Extract the OpenITI mARkdown page transcriptions and merge them into one file.
    
    Args:
        zip_fp (str): path to the zip file
        delete_zip (bool): if True, the original zip file will be deleted
            after the text was extracted from it
    
    Returns:
        None
    """
    # if a folder is passed as first argument instead of a zip file, convert all zip files in that folder:
    if not zip_fp.endswith(".zip"):
        for fn in os.listdir(zip_fp):
            print(fn)
            fp = os.path.join(zip_fp, fn)
            if fp.endswith(".zip"):
                main(fp, delete_zip=delete_zip)
        return

    # unzip the container zip file, which contains two nested zips
    # (the container will be the URI of the text):
    uri_folder = unzip_container(zip_fp)

    # find the zip file containing the openiti markdown page transcriptions:
    for root, dirs, files in os.walk(uri_folder):
        for fn in files:
            fp = os.path.join(root, fn)
            print(fp)
            if fp.endswith(".zip"):
                if "openitimarkdown" in fn:
                    # merge all openiti markdown page transcriptions into one text file:
                    merge_md(fp, uri_folder)
                    
                # better to convert tei from OpenITI mARkdown directly
                #elif "teixml" in fn:
                #    merge_tei(fp, uri_folder)
    
    # remove the original zip file and the temporary unzipped folder:
    shutil.rmtree(uri_folder)
    if delete_zip:
        os.remove(zip_fp)

    # remove the temporary extension of the OpenITI mARkdown file:
    os.rename(uri_folder+".txt", uri_folder)

if __name__ == "__main__":
    fp = r"0650QaysRazi.Mucjam.AOCP1017-per1.zip"
    main(".")