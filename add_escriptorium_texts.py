"""Add OCR'ed texts to barzakh.

Provide a tsv file that contains metadata on the files
(e.g., Google sheet: https://docs.google.com/spreadsheets/d/1SxMcgHuPCrUca2V0IO2zlQrkRR28T6DwErMCAVoDzTQ/edit#gid=0)
"""
import json
import os
import re
import csv
from shutil import copyfile
from openiti.helper.yml import readYML, dicToYML
from  openiti.helper.templates import version_yml_template, book_yml_template
import urllib.request

from escriptorium_connector import EscriptoriumConnector

from lxml import etree
import statistics
from zipfile import ZipFile
import time
import shutil
from openiti.helper.funcs import natural_sort
from datetime import datetime


escript_message = """This text was OCR'ed as part of the second phase of the\
¶    OpenITI AOCP project, generously funded by the Andrew W. Mellon Foundation."""
escript_version = "0.13.8"




def get_all_region_types_in_document(root, nsmap):
    """Get a list of all region types used in an document

    Args:
        root (Element): the root element of the XML document
        nsmap (dict): a dictionary containing the namespaces used in the document

    Returns:
        list
    """
    all_regions = set()
    for region in root.xpath("//default:TextRegion", namespaces=nsmap):
        region_type = get_region_type(region)
        all_regions.add(region_type)
    return list(all_regions)

def get_region_type(region_element):
    """Get the region type of a TextRegion element

    Args:
        text_line (Element): an etree TextRegion element

    Returns:
        str
    """
    region_type = region_element.get("custom")
    if region_type:
        region_type = re.findall("type:(\w+)", region_type)[0]
    return region_type

def choose_regions(regions, exclude_regions, root, nsmap):
    """Select which regions should be extracted from the XML document.

    Args:
        regions (list): a list of regions to be extracted
        exclude_regions (list): a list of regions to be excluded
        root (Element): the root element of the XML document
        nsmap (dict): a dictionary containing the namespaces used in the document

    Returns:
        list
    """
    all_region_types = get_all_region_types_in_document(root, nsmap)
    if regions == "all":
        #regions = all_region_types
        return "all"
    elif not regions:
        if exclude_regions:
            return [r for r in all_region_types if r not in exclude_regions]
        print("Do you want to extract all regions? Press Enter.")
        print("Alternatively, provide a comma-separated list of")
        print("the numbers of each region you want to include:")
        for i, r in enumerate(all_region_types):
            print("  {}. {}".format(i, r))
        resp = input()
        if not resp:
            regions = all_region_types
        else:
            regions = []
            for el in resp.split(","):
                #print(el, int(el.strip()))
                try:
                    regions.append(all_region_types[int(el.strip())])
                except:
                    pass
    return regions

def parse_lines(root, nsmap, regions, fp, exclude_regions=[],
                extremes_ratio=0.1, midpoint_ratio=0.6, skip_orphan_lines=True):
    """Parse the TextLine elements in the XML files as a dictionary

    Args:
        root (Element): the root element of the XML document
        nsmap (dict): a dictionary containing the namespaces used in the document
        regions (list): a list of regions to be extracted
        fp (str): path to the file containting the transcription
            (only for debugging printing)
        exclude_regions (list): a list of region names from which text should
            not be extracted
        extremes_ratio (float): the ratio of X coordinates that should be
            disregarded
        midpoint_ratio (float): The ratio of the horizontal midpoint of the line
            compared to the extremes of the line. To be used to determine
            whether a line segment contains the second hemistych of a poetry line

    Returns:
        list
    """
    lines = []
    region_xs = dict()
    line_heights = []
    for text_line in root.xpath("//default:TextLine", namespaces=nsmap):
        line_d = dict()
        
        # get the type of the region that contains the line:
        region = text_line.getparent()
        region_type = get_region_type(region)

        # skip orphan lines:
        if region_type is None and skip_orphan_lines:
            continue
        # skip lines that are in undesired regions:
        elif region_type in exclude_regions:
            continue
        # skip lines that are not in the whitelist of regions:
        elif (regions != "all" and region_type not in regions):
            continue

        line_d["region"] = region_type

        # get the text content of the line:
        line_text = etree.tostring(text_line, method="text", encoding='utf-8')
        line_d["text"] = line_text.decode("utf-8")
        
        # get the coordinates of the line:
        coords = text_line.find("default:Coords", nsmap)
        try:
            points = coords.get("points") # string of space-separated x,y pairs
        except:
            print(fp)
            print("No coordinates found in line", text_line.get("id"))
            print(etree.tostring(text_line))
            continue
        
        # store the bounding box values of the line mask:
        xs = [int(coord.split(",")[0]) for coord in points.split(" ")]
        line_d["min_x"] = min(xs)
        line_d["max_x"] = max(xs)
        ys = [int(coord.split(",")[1]) for coord in points.split(" ")]
        line_d["min_y"] = min(ys)
        line_d["max_y"] = max(ys)

        # calculate the line height and add it to the list:
        line_height = line_d["max_y"] - line_d["min_y"]
        line_heights.append(line_height)
        
        
##        # get the type of the region that contains the line:
##        region = text_line.getparent()
##        region_type = get_region_type(region)
##        print(line_d)
##        print(region, region_type)
##        line_d["region"] = region_type

        lines.append(line_d)


        if not region_type in region_xs:
            region_xs[region_type] = []
        region_xs[region_type] += xs
        #print(line_d)
        #print(region, region_type)


            
    # sort the regions by their horizontal position on the page:
    lines = sorted(lines, key=lambda d: (d["min_y"], d["max_x"]))

    # calculate the midpoint of the lines of each region
    # (to help decide whether a line segment is a second hemistych):
    region_midpoints = dict()
    for region in region_xs:
        all_xs = region_xs[region]
        # Remove the extremes on both sides:
        extremes = int(extremes_ratio * len(all_xs))
        if extremes > 1:
            all_xs = sorted(all_xs)[extremes:-extremes]
        #else:
            #print("too few x values to remove the extremes")
        try:
            midpoint = midpoint_ratio * (min(all_xs) + max(all_xs))
            #print(min(all_xs), midpoint, max(all_xs))
        except:
            midpoint = 0
        region_midpoints[region] = midpoint
    
    try:
        median_line_height = statistics.median(line_heights)
    except:
        median_line_height = None
    #print("median_line_height", median_line_height)
    return lines, region_midpoints, median_line_height

def sort_segments_per_line(line_segments, median_line_height, min_line_overlap=20):
    """Given a list of line dictionaries, sorted vertically from top to bottom,
    create a new list in which segments that are on the same line
    are in grouped in a list.

    NB: the zero point for both axes is in the left upper corner of the image!

    Args:
        line_segments (list): a list of line segment dictionaries,
            sorted vertically from top to bottom based their min_y coordinate
        median_line_height (int): median line height for this page
            (line height was calculated as max_y - min_y for each line mask)
        min_line_overlap (int): the number of pixels lines should overlap
            before their overlap is considered meaningful

    Returns:
        list of lists
    """
    try:
        min_line_overlap = max(median_line_height/3, min_line_overlap)
    except:
        min_line_overlap = None  # no lines found!

    
    prev_max_y = 0
    prev_max_x = 0
    prev_min_x = 0
    line = []
    lines = []
    for segm in line_segments:
        #print("segm", segm)
        #print("line height:",  segm["max_y"] - segm["min_y"])
        # first check vertical overlap between current and previous line:
        #print('segm["min_y"]', segm["min_y"])
        vertical_overlap = (prev_max_y - segm["min_y"]) > min_line_overlap
        #print("vertical_overlap", vertical_overlap)
        
        # then check horizontal overlap between current and previous line:
        #print('segm["max_x"]', segm["max_x"])
        if segm["max_x"] > prev_max_x:
            #horizontal_overlap = segm["min_x"] < prev_max_x
            horizontal_overlap = (prev_max_x - segm["min_x"]) > min_line_overlap
        else:
            #horizontal_overlap = segm["max_x"] > prev_min_x
            horizontal_overlap = (segm["max_x"] - prev_min_x) > min_line_overlap
        #print("horizontal_overlap", horizontal_overlap)
        #print("--------------")

        # Line segments are on the same line only if they overlap vertically
        # but not horizontally:  (NB: not sure about horizontal overlap!)
        if vertical_overlap and not horizontal_overlap:
            # add the segment to the current line
            line.append(segm)
        else:
            # store the previous line and start a new one:
            if line:
                # sort the segments based on their X coordinates
                # and append the line to the list of lines:
                lines.append(sorted(line, key=lambda d: d["min_x"], reverse=True))
            line = [segm, ]

        # store the current line's coordinates for comparison with the next line:
        prev_max_y = segm["max_y"]
        prev_max_x = segm["max_x"]
        prev_min_x = segm["min_x"]

    # add any line remaining after the end of the loop:
    if line:
        lines.append(sorted(line, key=lambda d: d["min_x"], reverse=True))
    
    return lines

def check_indentation(segm_d, indent_threshold):
    """Check whether a line is indented

    Args:
        segm_d (dict): a dictionary describing a line segment
        indent_threshold (int): the number of pixels
            (starting from the left of the page) that is considered
            the indentation threshold

    Returns:
        bool
    """
    if segm_d["max_x"] < indent_threshold:
        return True
    return False

def get_image_fn(root, nsmap):
    """Get the filename of the transcribed image from the XML metadata

    Args:
        root (Element): the root element of the XML document
        nsmap (dict): a dictionary containing the namespaces used in the document

    Returns:
        str
    """
    try:
        return root.find(".//default:Page", nsmap).get("imageFilename")
    except Exception as e:
        #print(e)
        return ""

def post_process(text, line_segment_separator):
    # remove empty lines:
    text = re.sub("\n~~(?:{})*\n".format(line_segment_separator), "\n", text)
    # remove line numbers:
    text = re.sub(line_segment_separator+"\d+\n", "\n", text)
    text = re.sub("(\n[# ~]+)\d+"+line_segment_separator, r"\1", text)
    # convert lines with a large indentation to titles:
    text = re.sub("# +%~% ", "### | ", text)
    
    return text

def switch_LR_pages(folder, ext="xml", rename_files=True, pad_zeros=False):
    """Switch pages that are in the wrong order in the folder: left page before right
    (usually something like page_2, page_1, page_4, page_3, ...)"""
    if rename_files:
        temp_dir = os.path.join(folder, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

    for filename in os.listdir(folder):
        if filename.endswith(ext):
            no = re.findall(r"\d+", filename)[-1]
            #print(no)
            if int(no)%2 == 1:
                if pad_zeros:
                    pattern = "{:0" + str(pad_zeros) +"d}"
                    new_filename = re.sub(str(int(no)), pattern.format(int(no)-2), filename)
                else:
                    new_filename = re.sub(str(int(no)), "{}".format(int(no)-2), filename)
            else:
                if pad_zeros:
                    pattern = "{:0" + str(pad_zeros) +"d}"
                    new_filename = re.sub(str(int(no)), pattern.format(int(no)), filename)
                else:
                    new_filename = filename
            #print(new_filename)
            if rename_files:
                os.rename(os.path.join(folder, filename), os.path.join(temp_dir, new_filename))
            #else:
            #    print(os.path.exists(os.path.join(folder, filename)))
    if rename_files:
        for fn in os.listdir(temp_dir):
            os.rename(os.path.join(temp_dir, fn), os.path.join(folder, fn))
        time.sleep(1)
        os.rmdir(temp_dir)

def convert_file(fp, regions=[], exclude_regions=[], page_offset=0, min_line_overlap=20,
                 line_segment_separator="   ", include_image_name=True,
                 skip_orphan_lines=True, first_page=0, transcription_meta=dict()):
    """Convert a single eScriptorium Page XML file to OpenITI mARkdown

    Args:
        fp (str): path to the xml file
        regions (list): list of names of region types from which the
            text should be extracted
        exclude_regions (list): list of names of region types from which the
            text should NOT be extracted
        page_offset (int): the number that should be added to the
            page number mentioned in the file name
        min_line_overlap (int): the number of pixels two line segments
            should overlap before the overlap is considered meaningful
        line_segment_separator (str): the separator that should be
            used to separate line segments that are on the same line
        include_image_name (bool): if True, the name of the transcribed
            image will be included at the top of the page.
        reorder_pages (bool): If True: swap the right and left page
            of a double page
        skip_orphan_lines (bool): if True, lines that are not embedded
            in a (named) region will be discarded
        first_page (int): if the current file is the first page of a book,
            first_page will be the real page number of that page;
            else, it will be 0.

    Returns:
        tuple (metadata:str, page_text:str, regions:list)

    """
    #print(fp)
    with open(fp, mode="rb") as file:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(file, parser)
        #print(etree.tostring(tree)[:1000])
    root = tree.getroot()
    
    # create a namespace map
    # (so we can use the default namespace in our xpath/findall searches)
    nsmap = {k if k is not None else 'default':v for k,v in root.nsmap.items()}

    # Define the regions that should be included, if not defined yet:
    regions = choose_regions(regions, exclude_regions, root, nsmap)
    
    # extract relevant information about line segments and regions:
    repl = parse_lines(root, nsmap, regions, fp, exclude_regions=exclude_regions,
                       skip_orphan_lines=skip_orphan_lines)
    line_segments, region_midpoints, median_line_height = repl

    # group line segments that are horizontally on the same line:
    lines = sort_segments_per_line(line_segments, median_line_height)
    #input("continue?")

    # Format the lines: 
    page_text = ""
    try:
        median_start_x = statistics.median([line[0]["max_x"] for line in lines])
    except Exception as e:
        print(e)
        median_start_x = 0
    line_lengths = [line[0]["max_x"]-line[-1]["min_x"] for line in lines]
    try:
        median_line_length = statistics.median(line_lengths)
    except Exception as e:
        print(e)
        median_line_length = 0
    indent_offset = median_start_x - (0.03*median_line_length)
    #print("median_start_x:", median_start_x, "indent_offset:", indent_offset)
    for line in lines:
        line_text = ""
        #print("----------")
        for segm in line:
            #print('segm["min_x"]:', segm["min_x"], 'segm["max_x"]:', segm["max_x"])
            #print(segm["text"])
            if segm["region"] == "Title":
                line_text += "\n### | " + segm["text"].strip()
            elif     segm["region"] == "Main" \
                 and segm["max_x"] < region_midpoints["Main"]:
                line_text = "\n# " + line_text + " %~% " + segm["text"].strip()
                #print('segm["min_x"]:', segm["min_x"],
                #      'segm["max_x"]:', segm["max_x"],
                #      "midpoint:", region_midpoints["Main"])
            else:
                line_text += line_segment_separator + segm["text"].strip()
            
        if not line[0]["region"] == "Title":
            if check_indentation(line[0], indent_offset):
                line_text = "# " + line_text[len(line_segment_separator):]
            else:
                line_text = "~~" + line_text[len(line_segment_separator):]

        page_text += line_text + "\n"
        

    # add page number:
    page_no = re.findall("\d+", fp)[-1]
    if first_page:
        page_offset = first_page - int(page_no)
        if first_page < 0:
            page_offset += 1
    page_text += "\nPageV01P{:03d}\n\n".format(int(page_no)+page_offset)

    # add image filename:
    if include_image_name:
        image_fn = get_image_fn(root, nsmap)
        page_text = "![image filename](./{})\n\n".format(image_fn) + page_text

    # remove some conversion artifacts:
    page_text = post_process(page_text, line_segment_separator)

    #print(page_text)

    # extract metadata from text file:
    metadata = ""
    meta_el = root.find("default:Metadata", nsmap)
    for child in meta_el:
        #print(child.tag, child.text)
        tag = child.tag.split("}")[-1]
        content = child.text.strip()
        metadata += "#META# {}: {}\n".format(tag, content)

    # add metadata from transcription layer:
    for tag, content in transcription_meta.items():
        if content:
            metadata += "#META# {}: {}\n".format(tag.replace("_", " "), content)
    
    return metadata, page_text, regions, page_offset

def convert_folder(folder, outfp, regions=[], exclude_regions=[],
                   page_offset=0, min_line_overlap=20, extension="xml",
                   line_segment_separator="   ", include_image_name=True,
                   skip_orphan_lines=True, first_page=0, transcription_meta=dict()):
    """Convert a folder containing eScriptorium XML files
    to a single OpenITI mARkdown document

    Args:
        folder (str): path to the folder containing the xml files
        outfp (str): path to the output mARkdown file
        regions (list): list of names of region types from which the
            text should be extracted
        page_offset (int): the number that should be added to the
            page number mentioned in the file name
        min_line_overlap (int): the number of pixels two line segments
            should overlap before the overlap is considered meaningful
        line_segment_separator (str): the separator that should be
            used to separate line segments that are on the same line
        include_image_name (bool): if True, the name of the transcribed
            image will be included at the top of the page.

    Returns:
        tuple (metadata:str, page_text:str, regions:list)
    """
    text = ""
    for i, fn in enumerate(natural_sort(os.listdir(folder))):
        if not fn.endswith(extension) or fn.startswith("METS"):
            continue
        fp = os.path.join(folder, fn)
        if i != 0:
            first_page = 0
        metadata, page_text, regions, page_offset = convert_file(fp,
            regions=regions,
            exclude_regions=exclude_regions,
            page_offset=page_offset,
            min_line_overlap=min_line_overlap,
            line_segment_separator=line_segment_separator,
            include_image_name=include_image_name,
            skip_orphan_lines=skip_orphan_lines,
            first_page=first_page,
            transcription_meta=transcription_meta)
        text += page_text
    metadata = "######OpenITI#\n\n{}\n\n#META#Header#End#\n\n".format(metadata)
    text = metadata + text

    with open(outfp, mode="w", encoding="utf-8") as file:
        file.write(text)



def convert_zip(zip_fp, outfp, regions=[], exclude_regions=[],
                page_offset=0, min_line_overlap=20,
                line_segment_separator="   ", include_image_name=True,
                reorder_pages=False, skip_orphan_lines=True, first_page=0,
                transcription_meta=dict()):
    """Convert a zip file containing eScriptorium XML files
    to a single OpenITI mARkdown document

    Args:
        zip_fp (str): path to the xml file
        outfp (str): path to the output mARkdown file
        regions (list): list of names of region types from which the
            text should be extracted. Alternatively, the string "all"
            can be provided: in this case, text from all regions will
            be extracted (also from orphan lines).
        page_offset (int): the number that should be added to the
            page number mentioned in the file name
        min_line_overlap (int): the number of pixels two line segments
            should overlap before the overlap is considered meaningful
        line_segment_separator (str): the separator that should be
            used to separate line segments that are on the same line
        include_image_name (bool): if True, the name of the transcribed
            image will be included at the top of the page.
        reorder_pages (bool): If True: swap the right and left page
            of a double page
        skip_orphan_lines (bool): if True, lines that are not embedded
            in a (named) region will be discarded

    Returns:
        tuple (metadata:str, page_text:str, regions:list)
    """
    # create a temporary directory to store the xml files extracted
    # from the zip archive:
    temp_folder = zip_fp+"_temp"
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    # Extract the xml files from the zip archive to the temporary directory
    with ZipFile(zip_fp, "r") as file:
        file.extractall(temp_folder)

    # reorder pages if the left page is before the right page:
    if reorder_pages:
        switch_LR_pages(temp_folder, ext="xml", rename_files=True, pad_zeros=3)

    convert_folder(temp_folder, outfp, regions=regions,
                   exclude_regions=exclude_regions, page_offset=page_offset,
                   min_line_overlap=min_line_overlap,
                   line_segment_separator=line_segment_separator,
                   include_image_name=include_image_name,
                   skip_orphan_lines=skip_orphan_lines,
                   first_page=first_page, transcription_meta=transcription_meta)
    time.sleep(1)
    shutil.rmtree(temp_folder)

def download_transcriptions(escr, download_folder, output_type="pagexml", projects=None,  
                            document_names=None, transcription_layers=None,
                            redownload=False):
    """Download transcriptions from eScriptorium.

    Use the transcription_layers, projects and document_names arguments
    to define which transcription layers from which documents from which projects
    you want to download.

    Args:
        escr (obj): EscriptoriumConnector object
        download_folder (str): output folder for the downloaded zip files
        output_type (str): either "pagexml", "alto", "text", "teixml" or "openitimarkdown".
            Default: "pagexml".
        projects (list): list of project slugs (normalized version of the project name;
            the slug is listed among the properties of each project and in the URL of your project).
        document_names (list): list of the names of the documents
            from which you want to download the transcriptions.
            Defaults to None (download transcriptions from all documents
            in the selected projects).
        transcription_layers (list): names of the transcription layers you want to download.
            Defaults to None (download all transcription layers from the selected documents)

    Returns:
        None
    """
    if projects:
        projects = [re.sub("\W", "-", p.lower()) for p in projects]
    
    for doc in escr.get_documents().results:
        
        if not document_names or doc.name in document_names:
            project = doc.project
            if not projects or project in projects:
                print("Document:", doc.name, "(primary key:", doc.pk, ")")

                # get the document's primary key:
                document_pk = doc.pk                
                
                # get all parts (that is, pages) of the document:
                document_parts = escr.get_document_parts(document_pk).results
                
                # select the desired transcription layer:
                transcriptions = escr.get_document_transcriptions(document_pk)
                if transcription_layers:
                    # only download the desired transcription layers
                    print("TRANSCRIPTION LAYERS:")
                    try:
                        transcriptions = [t for t in transcriptions if t.name in transcription_layers]
                        print(transcriptions)
                        transcriptions[0]  # will fail if the transcription layer is not present
                    except IndexError :
                        print("None of the requested transcription layers is available")
                        continue  # skip this document

                # download each transcription layer separately as a zip file:
                print("Downloading transcription layer(s):")
                for t in transcriptions:
                    print("* {} (primary key: {})".format(t.name, t.pk))

                    # create the path to the download location:
                    normalized_transcription_layer = re.sub("""[/<>:"\\|?*]""", "_", t.name)
                    outfolder = os.path.join(download_folder,
                                             project,
                                             doc.name,
                                             normalized_transcription_layer)
                    if not os.path.exists(outfolder):
                        os.makedirs(outfolder)
                    if output_type == "text":
                        fp  = os.path.join(outfolder, "{}_{}.txt".format(doc.name, output_type))
                    else:
                        fp  = os.path.join(outfolder, "{}_{}.zip".format(doc.name, output_type))
                    #print(fp)

                    # store the transcription's metadata as a json file:
                    json_fp = outfolder + "_meta.json"
                    d = {"transcription_layer_pk": t.pk, "transcription_layer_name": t.name, "archived": t.archived, "avg_transcription_confidence": t.avg_confidence}
                    with open(json_fp, mode="w", encoding="utf-8") as file:
                        json.dump(d, file, ensure_ascii=False, indent=2)

                    if os.path.exists(fp) and not redownload:
                        continue
                
                    try:
                        # (this is currently only possible after removing the dunder ("__")
                        # before the `download_part_output_transcription` in the escriptorium.py source code):
                        output_zipped = escr.download_part_output_transcription(document_pk,
                                                                                [part.pk for part in document_parts],
                                                                                t.pk,
                                                                                output_type)
                    except:
                        if output_type == "pagexml":
                            output_zipped = escr.download_part_pagexml_transcription(document_pk,
                                                                                     [part.pk for part in document_parts],
                                                                                     t.pk)
                        elif output_type == "text":
                            output_zipped = escr.download_part_text_transcription(document_pk,
                                                                                  [part.pk for part in document_parts],
                                                                                  t.pk)
                        elif output_type == "alto":
                            output_zipped = escr.download_part_alto_transcription(document_pk,
                                                                                  [part.pk for part in document_parts],
                                                                                  t.pk)
                        else:
                            print("output type '{}' is currently not supported".format(output_type))
                            continue

##                    # create the path to the download location:
##                    normalized_transcription_layer = re.sub("""[/<>:"\\|?*]""", "_", t.name)
##                    outfolder = os.path.join(download_folder,
##                                             project,
##                                             doc.name,
##                                             normalized_transcription_layer)
##                    if not os.path.exists(outfolder):
##                        os.makedirs(outfolder)
##                    if output_type == "text":
##                        fp  = os.path.join(outfolder, "{}_{}.txt".format(doc.name, output_type))
##                    else:
##                        fp  = os.path.join(outfolder, "{}_{}.zip".format(doc.name, output_type))
##                    print(fp)
                    
                    # store the downloaded zip file at that path:
                    with open(fp,mode="wb") as file:
                        file.write(output_zipped)


                        
                    
    return fp


def add_to_yml(yml_fp, based, link, notes, issues, uri=None):
    yml = readYML(yml_fp)
    if based:
        yml["80#VERS#BASED####:"] = based
    if link:
        yml["80#VERS#LINKS####:"] = urllib.request.unquote(link)
    if notes:
        if not yml["90#VERS#COMMENT##:"].startswith("a free running comment"):
            yml["90#VERS#COMMENT##:"] += "¶    NOTE: " + notes
        else:
            yml["90#VERS#COMMENT##:"] = notes
    if not (yml["90#VERS#ISSUES###:"].startswith("formalized issues")):
        if issues:
            if not "UNCORRECTED_OCR" in issues:
                yml["90#VERS#ISSUES###:"] += "; UNCORRECTED_OCR; "  + issues
            else:
                yml["90#VERS#ISSUES###:"] += issues
        else:
            if not "UNCORRECTED_OCR" in issues:
                yml["90#VERS#ISSUES###:"] += "; UNCORRECTED_OCR"
    else:
        yml["90#VERS#ISSUES###:"] = "UNCORRECTED_OCR"
    if uri:
        yml["00#VERS#URI######:"] = uri
    with open(yml_fp, mode="w", encoding="utf-8") as file:
        file.write(dicToYML(yml))
  



def add_OCR_pipeline_files(meta_fp, ocr_folder, dest_folder):
    """Add files from the OCR pipeline to barzakh
    
    Args:
        meta_fp (str): path to the tsv file containing the metadata
        ocr_folder (str): path to the folder containing the transcriptions
        dest_folder (str): path to the output folder
    """
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

def add_eScriptorium_files(meta_fp, download_folder, dest_folder,
                           start_row=1, end_row=1000, coll_id="AOCP2",
                           regions=[], exclude_regions=["Footnotes",],
                           min_line_overlap=20, line_segment_separator="   ",
                           include_image_name=True, reorder_pages=False,
                           skip_orphan_lines=True, reconvert=False, redownload=False):
    """Add files from eScriptorium to barzakh
    
    Args:
        meta_fp (str): path to the tsv file containing the metadata
            (headers: "eScriptorium project name", "eScriptorium document name", 
            "eScriptorium transcription layer", "URI", "language code", "BASED LINK (WORLDCAT)", 
            "DOWNLOAD LINK", "SUBMITTED BY", "KITAB PIPELINE / eSCRIPTORIUM", "NOTES", 
            "ISSUES", "CHANGE URI TO", "PAGE NUMBER OF FIRST IMAGE", "BOOK RELATIONS", 
            "CORPUS/BARZAKH")
        download_folder (str): path to the folder to which the transcriptions should be downloaded
        dest_folder (str): path to the output folder
        start_row (int): first row in the metadata table to be processed
        end_row (int): last row in the metadata table to be processed
        coll_id (str): the collection ID that will become the first part of the version ID
        regions (list): a list of regions from which text needs to be extracted
        exclude_regions (list): a list of regions from which text needs to be dropped
        min_line_overlap (int): the number of pixels lines should overlap
            before their overlap is considered meaningful
        line_segment_separator (str): the separator that should be
            used to separate line segments that are on the same line. Default: "   "
        include_image_name (bool): if True, the name of the transcribed
            image will be included at the top of the page.
        reorder_pages (bool): If True: swap the right and left page
            of a double page
        skip_orphan_lines (bool): if True, lines that are not embedded
            in a (named) region will be discarded
        redownload (bool): if True, the transcriptions will be downloaded from eScriptorium
            even if they already exist in the download folder.
        reconvert (bool): if False, files that are already in barzakh or the corpus
            (according to the metadata file) will be skipped. If True, they will be
            convered again. 
    """
    escr = connect_to_escr()
    with open(meta_fp, mode="r", encoding="utf-8") as file:
        #meta = file.read().splitlines()
        #header = meta[0]
        reader = csv.DictReader(file, delimiter="\t")
        i = 1
        for row in reader:
            i += 1
            #print("row", i)
            
            # do not download/convert rows before start_row:
            if i < start_row:  
                #print(row["eScriptorium document name"])
                continue
            # do not download/convert already converted texts:
            elif (row["CORPUS/BARZAKH"] and not reconvert):  
                continue
            # do not download/convert texts after the end_row:
            elif i > end_row:
                break
            

            # download the transcription from eScriptorium:

            project = row["eScriptorium project name"]
            doc = row["eScriptorium document name"]
            layer = row["eScriptorium transcription layer"]
            zip_fp = download_transcriptions(escr, download_folder,
                                             output_type="pagexml",
                                             projects=[project,],
                                             document_names=[doc,],
                                             transcription_layers=[layer,],
                                             redownload=redownload)

            print("row", i)
            print(project, doc, layer)

            # get the transcription layer metadata:
            
            json_fp = os.path.split(zip_fp)[0] + "_meta.json"
            try:
                with open(json_fp, mode="r", encoding="utf-8") as json_file:
                    transcription_meta = json.load(json_file)
            except Exception as e:
                print("Failed loading transcription layer metadata:", e)
                transcription_meta = dict(transcription_layer_pk=None,
                                          transcription_layer_name=layer,
                                          avg_transcription_confidence=None)


            # build the output filename:
            
            if row["CHANGE URI TO"]:
                uri = row["CHANGE URI TO"]
            else:
                uri = row["URI"]
            lang = row["language code"]
            timestamp = datetime.utcnow().strftime("%y%m%d")
            fn = f"{uri}.{coll_id}0{timestamp}{i:02d}-{lang}1"
            #print(fn)
            outfp = os.path.join(dest_folder, fn)
            #print(outfp)

            # convert the xml files into an OpenITI mARkdown file:
            
            try:
                first_page = int(row["PAGE NUMBER OF FIRST IMAGE"])
            except:
                first_page = 0
            convert_zip(zip_fp, outfp, regions=regions,
                        exclude_regions=exclude_regions,
                        page_offset=0,
                        min_line_overlap=min_line_overlap,
                        line_segment_separator=line_segment_separator,
                        include_image_name=include_image_name,
                        reorder_pages=reorder_pages,
                        skip_orphan_lines=skip_orphan_lines,
                        first_page=first_page, transcription_meta=transcription_meta)

            # create a version yml file and store it:
            yml_fp = outfp + ".yml"
            with open(yml_fp, mode="w", encoding="utf-8") as file:
                file.write(version_yml_template)

            # fill in relevant YML fields:
            based = row["BASED LINK (WORLDCAT)"]
            link = row["DOWNLOAD LINK"]
            issues = row["ISSUES"]
            submitter = row["SUBMITTED BY"]
            notes = escript_message + "¶    This file was created on "
            notes += datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            notes += " by eScriptorium version " + escript_version
            notes += "¶    Transcription model used: " + layer.strip("kraken:")
            if "avg_transcription_confidence" in transcription_meta:
                avg_confidence = transcription_meta["avg_transcription_confidence"]
                if avg_confidence:
                    notes += f"¶    Average transcription confidence: {avg_confidence}"
                    
            if row["NOTES"]:
                notes += "¶    " + row["NOTES"]
            add_to_yml(yml_fp, based, link, notes, issues, uri=fn)

            # create a book YML file if the metadata contains book relations:
            relations = row["BOOK RELATIONS"]
            book_uri = ".".join(uri.split(".")[:2])
            if relations:
                yml_fp = os.path.join(dest_folder, book_uri + ".yml")
                with open(yml_fp, mode="w", encoding="utf-8") as file:
                    file.write(book_yml_template)
                yml_d = readYML(yml_fp)
                yml_d["00#BOOK#URI######:"] = book_uri
                yml_d["40#BOOK#RELATED##:"] = relations
                with open(yml_fp, mode="w", encoding="utf-8") as file:
                    file.write(dicToYML(yml_d))
            
            
def connect_to_escr():
    """Establish a connection to eScriptorium

    Returns:
        escr (an eScriptorium connection object)
    """
    try:
        # load your credentials from the .env file if it exists:
        from dotenv import load_dotenv
        load_dotenv()

        username = str(os.getenv("ESCRIPTORIUM_USERNAME"))
        password = str(os.getenv("ESCRIPTORIUM_PASSWORD"))
        url = str(os.getenv("ESCRIPTORIUM_URL"))
    except:
        # ask user to provide username and password manually:
        username = input("Please provide your eScriptorium username: ")
        password = input("Please provide your eScriptorium password: ")
        print("If you don't want to use the default eScriptorium page")
        print("(https://escriptorium.openiti.org/)")
        url = input("please provide the URL of your eScriptorium instance (press Enter to use the default):").strip()

    if not url:
        url = "https://escriptorium.openiti.org/"

    escr = EscriptoriumConnector(url, username, password)
    return escr



            
        


if __name__ == "__main__":
    meta_fp = "meta/Corpus_Metadata_Links.tsv" # Google sheet: https://docs.google.com/spreadsheets/d/1SxMcgHuPCrUca2V0IO2zlQrkRR28T6DwErMCAVoDzTQ/edit#gid=0
    meta_fp = "meta/Corpus_Metadata_Links - new to be added.tsv"
    meta_fp = "meta/OCR_URIs_2022_2023 - ESCRIPTORIUM.tsv"
    meta_fp = "meta/OCR_URIs_2022_2023 - ESCRIPTORIUM_Suluk.tsv"
    


    download_folder = "eScriptorium_pagexml"
    dest_folder = "."
    add_eScriptorium_files(meta_fp, download_folder, dest_folder,
                           #reconvert=True,             # convert even if the file is already in the corpus or barzakh
                           #start_row=28, end_row=28,   # from row X to row Y in the metadata file
                           #redownload=True
                           )
