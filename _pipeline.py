"""This script provides a pipeline that

* checks if the URI of each text file is well-formed, the collection is known 
* checks whether the text file has either no extension or a known extension
* checks if text files contain an OpenITI header
* checks for unallowed characters in text files in the folder
  (based on the language component of the URI)
* removes any existing milestone IDs and creates new ones
* checks present yml files are well-formed
* moves text (and if present, yml) files to the corpus folders

"""
import math
import os
import pandas as pd
import re
import textwrap
import unicodedata

from openiti.helper.ara import normalize_composites, denoise, allowed_chars_regex, unwanted_chars_regex, ar_tok_cnt, ar_tok, decode_unicode_name
from openiti.helper.rgx import auth, book, version
from openiti.helper.yml import readYML, fix_broken_yml, dicToYML
from openiti.new_books.add.add_books import initialize_new_text


author_uri_regex = auth
book_uri_regex = book
version_uri_regex = version

# list of collection names in which line endings of texts should be kept as is:
keep_line_endings_ids = "|".join(["eScr", "EScr", "Kraken", "Tess", "GVDB"])


def get_known_collections():
    """Get a tuple containg all known source collections of OpenITI texts from OpenITI metadata
    
    Returns:
        tup
    """
    meta_url = "https://github.com/OpenITI/kitab-metadata-automation/raw/master/output/OpenITI_Github_clone_metadata_light.csv"
    df = pd.read_csv(meta_url, sep="\t")
    known_collections = tuple()
    for coll in sorted(list(set([re.findall("[a-zA-Z]+", id_)[0] for id_ in df["id"]]))):
        known_collections = known_collections + (coll, )
    return known_collections

try:
    known_collections = get_known_collections()
except: 
    known_collections = (
        'ALCorpus',
        'AQ',
        'ArabCommAph',
        'BibleCorpus',
        'DARE',
        'ER',
        'EScr',
        'EShia',
        'Filaha',
        'GRAR',
        'GVDB',
        'Hindawi',
        'JK',
        'JMIHE',
        'JT',
        'Kalema',
        'KetabOnline',
        'Khismatulin',
        'Kraken',
        'LMN',
        'MAB',
        'MMS',
        'MSG',
        'Masaha',
        'Meshkat',
        'NH',
        'NLIAG',
        'Noorlib',
        'Other',
        'PAL',
        'PES',
        'PV',
        'Qaemiyeh',
        'QuranAnalysis',
        'Rafed',
        'SAWS',
        'Sham',
        'ShamAY',
        'ShamDhahabiyya',
        'ShamDhayabiyya',
        'ShamIbadiyya',
        'Shamela',
        'Shia',
        'SyriacStudies',
        'Tafsir',
        'Tanzil',
        'Tess',
        'WG',
        'Wiki',
        'Zaydiyya',
        'eScr',
    )

print(known_collections)

# Create replacement tuples for cleaning text:

# first, create some variables for a couple of special characters: 

HAMZA_ABOVE = "ٔ"
HAMZA_BELOW = "ٕ"
MADDAH_ABOVE = "ٓ"
SMALL_MADDAH = "ۤ"
# zw = """\
# ‌	ZERO WIDTH NON-JOINER
# ‍	ZERO WIDTH JOINER
# """
# ZWNJ = [x.split("\t")[0] for x in zw.splitlines()][0]
# ZWJ  = [x.split("\t")[0] for x in zw.splitlines()][1]
ZWNJ = decode_unicode_name("ZERO WIDTH NON-JOINER")
ZWJ = decode_unicode_name("ZERO WIDTH JOINER")

# then, build replacement tuples for (combinations of) characters 
# that should be replaced in any text:

# repl_tup = [
#     ("…", "..."),
#     ("٭", "*"),   # ARABIC FIVE POINTED STAR
#     ("∗", "*"),   # ASTERISK OPERATOR
#     ("❊", "*"),   # EIGHT TEARDROP-SPOKED PROPELLER ASTERISK
#     ("٠", "0"),   # ARABIC-INDIC DIGITs
#     ("١", "1"),
#     ("٢", "2"), 
#     ("٣", "3"),
#     ("٤", "4"),
#     ("٥", "5"),
#     ("٦", "6"),
#     ("٧", "7"),
#     ("٨", "8"),
#     ("٩", "9"),
#     ("۰", "0"),   # EXTENDED ARABIC-INDIC DIGITs
#     ("۱", "1"),
#     ("۲", "2"), 
#     ("۳", "3"),
#     ("۴", "4"),
#     ("۵", "5"),
#     ("۶", "6"),
#     ("۷", "7"),
#     ("۸", "8"),
#     ("۹", "9"),
#     ("–", "-"),   # EN DASH
#     ("—", "-"),   # EM DASH
#     ("۔", "."),   # ARABIC FULL STOP
#     ("⁄", "/"),   # FRACTION SLASH
#     ("ھ", "ه"),   # ARABIC LETTER HEH DOACHASHMEE
#     ("ٱ", "ا"),   # U+0671 , ARABIC LETTER ALEF WASLA
#     ("ا"+MADDAH_ABOVE, "آ"),
#     #(MADDAH_ABOVE+"ا", "آ"),
#     (MADDAH_ABOVE+"أ", "اأ"),  # in Qur'ān, e.g. yā-ayyuhā
#     #(MADDAH_ABOVE+"أ", "آ"),
#     ("أ"+MADDAH_ABOVE, "آ"),
#     (MADDAH_ABOVE, ""),

#     ("ا"+SMALL_MADDAH, "آ"),
#     (SMALL_MADDAH+"ا", "آ"),
#     ("أ"+SMALL_MADDAH, "آ"),
#     (SMALL_MADDAH+"أ", "آ"),
#     (SMALL_MADDAH, ""),

#     ("ا"+HAMZA_BELOW, "إ"),
#     (HAMZA_BELOW+"ا", "إ"),
#     (HAMZA_BELOW, "")

#     ("ا"+HAMZA_ABOVE, "أ"),
#     #(HAMZA_ABOVE+"ا", "أ"),
#     ("و"+HAMZA_ABOVE, "ؤ"),
#     #(HAMZA_ABOVE+"و", "ؤ"),
#     ("ى"+HAMZA_ABOVE, "ئ"),
#     #(HAMZA_ABOVE+"ى", "ئ"),
#     (HAMZA_ABOVE+"ا", "آ"), 
#     (HAMZA_ABOVE, "آ"),  # in Qur'ān often in combination with dagger alif for alif + madda: الٔن  for الآن

#     ("﻿", ""),   # ZERO WIDTH NO-BREAK SPACE [ZWNBSP] (alias BYTE ORDER MARK [BOM])

#     ]

repl_tup = [
    ("…", "..."), # HORIZONTAL ELLIPSIS
    ("٭", "*"),   # ARABIC FIVE POINTED STAR
    ("∗", "*"),   # ASTERISK OPERATOR
    ("❊", "*"),  # EIGHT TEARDROP-SPOKED PROPELLER ASTERISK
    ("✧", "*"),  # WHITE FOUR POINTED STAR
    ("﴾", "("),   # ORNATE LEFT PARENTHESIS
    ("﴿", ")"),   # ORNATE RIGHT PARENTHESIS
    ("→", "->"),   # RIGHTWARDS ARROW
    ("ʼ", "'"),   # MODIFIER LETTER APOSTROPHE
    ("‘", "'"),   # LEFT SINGLE QUOTATION MARK
    ("٠", "0"),   # ARABIC-INDIC DIGITs
    ("١", "1"),
    ("٢", "2"), 
    ("٣", "3"),
    ("٤", "4"),
    ("٥", "5"),
    ("٦", "6"),
    ("٧", "7"),
    ("٨", "8"),
    ("٩", "9"),
    ("۰", "0"),   # EXTENDED ARABIC-INDIC DIGITs
    ("۱", "1"),
    ("۲", "2"), 
    ("۳", "3"),
    ("۴", "4"),
    ("۵", "5"),
    ("۶", "6"),
    ("۷", "7"),
    ("۸", "8"),
    ("۹", "9"),
    ("–", "-"),   # EN DASH
    ("—", "-"),   # EM DASH
    ("۔", "."),   # ARABIC FULL STOP
    ("⁄", "/"),   # FRACTION SLASH
    ("ھ", "ه"),   # ARABIC LETTER HEH DOACHASHMEE
    ("ٱ", "ا"),   # U+0671 , ARABIC LETTER ALEF WASLA

    ("ARABIC LETTER ALEF_ARABIC MADDAH ABOVE", "آ"),
    ("ARABIC MADDAH ABOVE_ARABIC LETTER ALEF WITH HAMZA ABOVE", "اأ"),  # in Qur'ān, e.g. yā-ayyuhā
    ("ARABIC LETTER ALEF WITH HAMZA ABOVE_ARABIC MADDAH ABOVE", "اأ"),
    ("ARABIC MADDAH ABOVE", ""),

    ("ا"+SMALL_MADDAH, "آ"),
    (SMALL_MADDAH+"ا", "آ"),
    ("أ"+SMALL_MADDAH, "آ"),
    (SMALL_MADDAH+"أ", "آ"),
    (SMALL_MADDAH, ""),

    ("ا"+HAMZA_BELOW, "إ"),
    (HAMZA_BELOW+"ا", "إ"),
    (HAMZA_BELOW, ""),

    ("ا"+HAMZA_ABOVE, "أ"),
    #(HAMZA_ABOVE+"ا", "أ"),
    ("و"+HAMZA_ABOVE, "ؤ"),
    #(HAMZA_ABOVE+"و", "ؤ"),
    ("ى"+HAMZA_ABOVE, "ئ"),
    #(HAMZA_ABOVE+"ى", "ئ"),
    (HAMZA_ABOVE+"ا", "آ"), 
    (HAMZA_ABOVE, "آ"),  # in Qur'ān often in combination with dagger alif for alif + madda: الٔن  for الآن

    ("ZERO WIDTH NO-BREAK SPACE", ""),   # (alias BYTE ORDER MARK [BOM])
    (ZWJ, ""),  # ZERO WIDTH JOINER
    ("ZERO WIDTH NO-BREAK SPACE", " "),  
    ("LEFT-TO-RIGHT MARK", ""),

    ]

repl_tup = [(decode_unicode_name(k), decode_unicode_name(v)) for k,v in repl_tup]
repl_dict = {k:v for k,v in repl_tup}


# finally, replace some glyphs in a specific language only:
# (based partly on https://scripts.sil.org/cms/scripts/render_download.php?format=file&media_id=arabicletterusagenotes&filename=ArabicLetterUsageNotes.pdf)

# repl_tup_ara = [    # Persian/Urdu glyphs for Arabic letters, normalized in Arabic texts:
#     ("ک", "ك"),   
#     ("ی", "ي"),
#     ("ے", "ي"),
#     ("ۓ", "ئ"),
#     ("ڭ", "ك"),
#     ("ں", "ن"),
#     ("ھ", "ه"),     # ARABIC LETTER HEH DOACHASHMEE
#     ("ہ", "ه"),     # ARABIC LETTER HEH GOAL
#     ("ۂ", "ه"),     # ARABIC LETTER HEH GOAL WITH HAMZA ABOVE
#     ("ۀ", "ه"),     # ARABIC LETTER HEH WITH YEH ABOVE
#     (ZWNJ, ""),     # ZERO WIDTH NON JOINER
#     (HAMZA_ABOVE, ""),
#     ]

# repl_tup_per = [    # Arabic glyphs not used for Persian:
#     ("ك", "ک"),   
#     ("ي", "ی"),
#     ("ے", "ی"),
#     ("ى", "ی"),     # Alif maksura
#     ("ۓ", "ئ"),
#     ("ڭ", "گ"),
#     ("ں", "ن"),
#     ("ھ", "ه"),     # ARABIC LETTER HEH DOACHASHMEE
#     ("ہ", "ه"),     # ARABIC LETTER HEH GOAL
#     ("﻿", ZWNJ),     # ZERO WIDTH NO-BREAK SPACE [ZWNBSP] (alias BYTE ORDER MARK [BOM])
#     ("ۂ"+ZWNJ+"?", "ه"+HAMZA_ABOVE+ZWNJ), # ARABIC LETTER HEH GOAL WITH HAMZA ABOVE
#     ("ۀ"+ZWNJ+"?", "ه"+HAMZA_ABOVE+ZWNJ), # ARABIC LETTER HEH WITH YEH ABOVE
#     ]

repl_tup_ara = [    # Persian/Urdu glyphs for Arabic letters, normalized in Arabic texts:
    ("ک", "ك"),     # ("ARABIC LETTER KEHEH", "ARABIC LETTER KAF")
    ("ی", "ي"),     # ("ARABIC LETTER FARSI YEH", "ARABIC LETTER YEH")
    ("ے", "ي"),     # ("ARABIC LETTER YEH BARREE", "ARABIC LETTER YEH")
    ("ۓ", "ئ"),     # ("ARABIC LETTER YEH BARREE WITH HAMZA ABOVE", "ARABIC LETTER YEH WITH HAMZA ABOVE")
    ("ڭ", "ك"),     # ("ARABIC LETTER NG", "ARABIC LETTER KAF")
    ("ں", "ن"),     # ("ARABIC LETTER NOON GHUNNA", "ARABIC LETTER NOON")
    ("ھ", "ه"),     # ("ARABIC LETTER HEH DOACHASHMEE", "ARABIC LETTER HEH")
    ("ہ", "ه"),     # ("ARABIC LETTER HEH GOAL", "ARABIC LETTER HEH")
    ("ۂ", "ه"),     # ("ARABIC LETTER HEH GOAL WITH HAMZA ABOVE", "ARABIC LETTER HEH")
    ("ۀ", "ه"),     # ("ARABIC LETTER HEH WITH YEH ABOVE", "ARABIC LETTER HEH")
    (ZWNJ, ""),     # ZERO WIDTH NON JOINER
    (HAMZA_ABOVE, ""),
    ]

repl_tup_per = [    # Arabic glyphs not used for Persian:
    ("ك", "ک"),     # ("ARABIC LETTER KAF", "ARABIC LETTER KEHEH")
    ("ي", "ی"),     # ("ARABIC LETTER YEH", "ARABIC LETTER FARSI YEH")
    ("ے", "ی"),     # ("ARABIC LETTER YEH BARREE", "ARABIC LETTER FARSI YEH")
    ("ى", "ی"),     # ("ARABIC LETTER ALEF MAKSURA", "ARABIC LETTER FARSI YEH")
    ("ۓ", "ئ"),     # ("ARABIC LETTER YEH BARREE WITH HAMZA ABOVE", "ARABIC LETTER YEH WITH HAMZA ABOVE")
    ("ڭ", "گ"),     # ("ARABIC LETTER NG", "ARABIC LETTER GAF")
    ("ں", "ن"),     # ("ARABIC LETTER NOON GHUNNA", "ARABIC LETTER NOON")
    ("ھ", "ه"),     # ("ARABIC LETTER HEH DOACHASHMEE", "ARABIC LETTER HEH")
    ("ہ", "ه"),     # ("ARABIC LETTER HEH GOAL", "ARABIC LETTER HEH")
    ("﻿", ZWNJ),     # ZERO WIDTH NO-BREAK SPACE [ZWNBSP] (alias BYTE ORDER MARK [BOM])
    ("ۂ"+ZWNJ+"?", "ه"+HAMZA_ABOVE+ZWNJ), # ARABIC LETTER HEH GOAL WITH HAMZA ABOVE
    ("ۀ"+ZWNJ+"?", "ه"+HAMZA_ABOVE+ZWNJ), # ARABIC LETTER HEH WITH YEH ABOVE
    ]

repl_tup_urd = [
    ("ك", "ک"),     # ("ARABIC LETTER KAF", "ARABIC LETTER KEHEH")
    ("ي", "ی"),     # ("ARABIC LETTER YEH", "ARABIC LETTER FARSI YEH")
    ("ى", "ی"),     # ("ARABIC LETTER ALEF MAKSURA", "ARABIC LETTER FARSI YEH")
    ]


def ask_replace_permission(text, pattern, repl, auto=False):
    if auto:
        return re.sub(pattern, repl, text)
    matches = re.findall(".*"+pattern+".*", text)
    if matches:
        for m in matches[:10]:
            print(m)
        print("I will replace this pattern:", [pattern])
        for c in pattern:
            print("   ", c, "\t", unicodedata.name(c))
        print("By:")
        for c in repl:
            print("   ", c, "\t", unicodedata.name(c))
        print("(found", len(matches), "times in the text")
        r = input("Agree? Y/N: ")
        if r.lower() == "y":
            text = re.sub(pattern, repl, text)
    return text


def milestone(text, fn, prev_ms=0, ms_length=300):
    """Add milestones to the text
    
    Args:
        text (str): the content of the text files, with old milestone tags removed
        fn (str): filename of the text file
        prev_ms (int): number of the last milestone in the previous text. Default: 0.
        ms_length (int): number of tokens in a milestone
    
    Returns: 
        tup (str, int)
    """
    #ara_tok = re.compile("^[ذ١٢٣٤٥٦٧٨٩٠ّـضصثقفغعهخحجدًٌَُلإإشسيبلاتنمكطٍِلأأـئءؤرلاىةوزظْلآآ]+$")

    # Check whether the milestone numbering should continue from another text file
    # (that is, the filename ends with)
    version_id = fn.split("-")[0].split(".")[-1]
    if re.search("[A-Z]$", version_id):
        continuous = version_id[-1]
    else:
        continuous = False

    # make sure the last milestone will not be added on a new line: 
    text = text.rstrip()

    # find the number of digits in the milestone IDs based on the last milestone number:
    ara_toks_count = ar_tok_cnt(text)
    ms_tag_str_len = len(str(math.floor(ara_toks_count / ms_length)))

    # Insert the milestones:
    all_toks = re.findall(r"\w+|\W+", text)

    token_count = 0
    if continuous and version_id[-1] != "A":
        ms_count = prev_ms
    else:
        ms_count = 0

    new_data = []

    for i in range(0, len(all_toks)):
        #if ara_tok.search(all_toks[i]):  
        if re.fullmatch(ar_tok, all_toks[i]):  # only Arabic tokens count for milestoning!
                                               # an Arabic token is every token that consists
                                               # entirely of Arabic letters or numbers
            token_count += 1
        new_data.append(all_toks[i])
        
        # Insert milestone tag after ms_length Arabic tokens (and at the end of the text):
        if token_count == ms_length or i == len(all_toks) - 1:
            ms_count += 1
            if continuous:  # use the pattern msA001
                milestone = " ms" + version_id[-1] + str(ms_count).zfill(ms_tag_str_len)
            else:           # use the pattern ms001
                milestone = " ms" + str(ms_count).zfill(ms_tag_str_len)
            new_data.append(milestone)
            token_count = 0

    ms_text = "".join(new_data)

    # check whether the text has been damaged by adding the milestones:
    test = re.sub(" ms([A-Z])?\d+", "", ms_text)
    # test = re.sub(" +", " ", test)
    if test == text:
        #print("\t\tThe file has not been damaged!")
        ms = re.findall("ms[A-Z]?\d+", ms_text)
        #print("\t\t%d milestones (%d words)" % (len(ms), ms_length))
        return ms_text, ms_count
    else:
        print("\t\tMilestoning damaged the text. Rolling back...")
        return text, None


def post_process(text):
    """Final cleaning of replacement artifacts in the text file
    
    Args:
        text (str): content of the text file
    
    Returns:
        str
    """
    text = re.sub(" ###", "\n\n###", text)
    #text = re.sub(r"(#META#Header#End#)~~[ \r\n]+~~", r"\1\n\n# ", text)
    #text = re.sub("(#META#Header#End#)~~[ \r\n]+", r"\1\n\n", text)
    text = re.sub(r"\A~~[ \r\n]+~~", r"\n\n# ", text)
    text = re.sub(r"\A~~[ \r\n]+", r"\n\n", text)
    text = re.sub(r"[\r\n]+~~ *(?:[\r\n]+|\Z)", "\n", text)
    text = re.sub("(?<=# |~~) *ا\s+| +ا *(?=[\r\n])", "", text) # fix leading and trailing alif issue (OCR)
    text = re.sub("~~ ", "~~", text)
    text = re.sub(r"\b([وفبلك]*(?:ا?ل)?)شئ\b", r"\1شيء", text)  # al-shay'
    return text

def add_paragraph_marks(text, keep_line_endings=True, maxlength=72):
    """Add paragraph marks (hashtags and tildas) to one file.

    Args:
        text (str): text as string
        keep_line_endings (bool): if True, line endings in the original file
            will be kept; if False, long lines will be broken into
            shorter lines.
        maxlength (int): maximum number of characters per line
    
    Returns:
        str
    """

    # add # after line that ends with full stop, question and exclamation marks:
    perhaps_page_or_ms = r"(?:[\r\n]*(?:PageV\w{2}P\d+[abAB]?|ms\d+) *)*"
    ptrn = r"([.؟!] *"+perhaps_page_or_ms+r"[\r\n]+)([^\r\n#P])"
    text = re.sub(ptrn, r"\1# \2", text)

    # add # after section titles (but not before page numbers and sub-titles)
    ptrn = r"(### .+"+perhaps_page_or_ms+r"[\r\n]+)([^\r\n#P])"
    text = re.sub(ptrn, r"\1# \2", text)

    if keep_line_endings:
        #  add the tildas for continued lines:
        new_text = ""
        for line in re.split(r"([\r\n]+)", text):
            if not line.startswith(("P", "#", "~~")) \
               and not re.match(r"[\r\n]+", line):
                line = "~~"+line
            new_text += line
    else:
        # move page number to the previous line:
        ptrn = r"([^ \r\n.؟!]) *[\r\n]+(PageV[^P]+P[\w]+) *[\r\n]+"
        text = re.sub(ptrn, r"\1 \2\n", text)
        # Add paragraph signs before every new line:
        ptrn = r"(\A|[\r\n]+)([^\r\n#P\s])"
        text = re.sub(ptrn, r"\1# \2", text)
        # break long lines into shorter lines:
        new_text = wrap(text, maxlength)

    # Fix cases where tildes were introduced before hashtags:
    new_text = re.sub("~~#", "#", new_text)
    # Fix cases where tildes were introduced before a line of poetry:
    new_text = re.sub(r"~~(.+?%~%)", r"# \1", new_text)
    # disregard "parent folder" pattern:
    new_text = re.sub(r"~~\.\./", "../", new_text)

    return new_text

def wrap(text, max_length=72, wrapped_line_marker="\n~~"):
    """Limit the length of lines.
    
    Args:
        text (str): the content of the text file
        max_length (int): the maximum number of characters per line
        wrapped_line_marker (str): the string inserted at the end of each wrapped line
    
    Returns:
        str
    """
    wrapped = []
    for line in re.split("([\r\n]+)", text):
        if line.startswith(("###", "\r", "\n")):
            wrapped.append(line)
        else:
            lines = textwrap.wrap(line, max_length, break_long_words=False)
            wrapped.append(wrapped_line_marker.join(lines))

    return "".join(wrapped)

def check_paragraph_marks(text, fn):
    """Check whether paragraphs are marked using OpenITI mARkdown `# ` and `~~` tags
    
    Args:
        text (str): content of the text file
    """
    # add paragraph marks:
    if not re.search("~~", text) or not re.search("^# ", text):
        if re.findall(keep_line_endings_ids, fn):
            text = add_paragraph_marks(text, keep_line_endings=True)
        else:
            text = add_paragraph_marks(text, keep_line_endings=False)
##    if editor:
##        text = re.sub("INSERT_EDITOR", editor, text)

    return text



def check_meta_header(text):
    """Check the presence of the OpenITI metadata header
    
    Args: 
        text (str): content of the text file
    
    Returns:
        str
    """
    # check if the magical value at the top of the document is present:
    if not text.strip().startswith("######OpenITI#"):
        if not "#META#Header#End#" in text:
            # if neither the start nor end of the header is present, add an empty header:
            text = "######OpenITI#\n\n#META#Header#End#\n"+text.strip()
        else:
            # if only the end of the header is found, raise an issue:
            print("START OF HEADER NOT FOUND!")
            print("Text starts with:", text[:20])
            return None, text
    # Check if the end of the metadata header is present:
    try:
        header, text = re.split("#META#Header#End#", text, maxsplit=1)
        return header, text
    except:
        print("END OF HEADER NOT FOUND!")
        return None, text

def clean(text, fn, auto=False):
    """Clean the text of a new OpenITI text
    
    Args:
        text (str): content of the text file
        fn (str): file name of the text file
        auto (bool): if True, all unallowed files will automatically be replaced;
            if False, user input will be asked for each file
            
    Returns:
        str
    """

    # remove unwanted characters from text:
    text = denoise(text)
    text = normalize_composites(text)

    # replace all patterns for which an auto replacement has been defined:

    # first, general replacement patterns
    for pattern, repl in repl_tup:
        text = ask_replace_permission(text, pattern, repl, auto)
    
    # second, replacement patterns for specific languages:
    if re.findall("-(?:[a-z]{3})*ara", fn):  # Arabic
        for pattern, repl in repl_tup_ara:
            print([pattern])
            text = ask_replace_permission(text, pattern, repl, auto)
    if re.findall("-(?:[a-z]{3})*per", fn):  # Persian
        print("Going through replacement patterns for Persian text...")
        for pattern, repl in repl_tup_per:
            text = ask_replace_permission(text, pattern, repl, auto)
    if re.findall("-(?:[a-z]{3})*urd", fn):  # Urdu
        print("Going through replacement patterns for Urdu text...")
        for pattern, repl in repl_tup_urd:
            text = ask_replace_permission(text, pattern, repl, auto)

    # replace all remaining unwanted characters:
    if auto:
        text = re.sub(unwanted_chars_regex, "", text)
    else:
        all_chars = "".join(set(text))
        filtered_chars = re.sub(allowed_chars_regex, "", all_chars)
        print("REMAINING SUSPICIOUS CHARACTERS AFTER FIRST CLEANING:", len(filtered_chars))
        not_found = []
        for c in sorted(filtered_chars):
            # print the character and its unicode name (if found)
            try:
                print(c, "\t", unicodedata.name(c))
            except:
                print(c, "\t(unicode name for this character not found)")
            # print the first 10 examples of the use of the character in the text:
            print("Examples of the character's use in the text (character highlighted with kashidas):")
            for x in re.findall("[^%s]{,20}ـــ%sـــ+[^%s]{,20}"%(c,c,c), text)[:10]:
                print(x)
                print("-"*30)
            print("({} times present in the text)".format(len(re.findall(c, text))))
            resp = input("Do you want to replace all? Y/n  ")
            if not resp.lower() == "n":
                if c in repl_dict:
                    text = re.sub(c, repl_dict[c], text)
                else:
                    print("What character do you want to replace it by? ")
                    r = input("(None if you don't want to replace)  ")
                    if r != "None":
                        text = re.sub(c, r, text)
                print("replaced", unicodedata.name(c))

    return text


def rewrap(text, maxlength=72):
    """Limit the length of lines"""
    text = re.sub("(### \|+.+[\r\n]+)([^#PN])", r"\1# \2", text)
    text = re.sub("[\r\n]+~~", " ", text)
    text = re.sub("[\r\n]+([^P#N])", r" \1", text)
    s = re.split("([\r\n]+)", text)
    new = ""
    for el in s:
        #print(el)
        if not el.strip(): # add empty lines
            new += el
        elif not el.startswith("##"):
            #print(textwrap.wrap(el))
            new += "\n~~".join(textwrap.wrap(el, maxlength))
        else:
            new += el
    #new = re.sub("([\r\n]+)([^P#~])", r"\1# \2", new)
    print(new)
    r = input("DOES THIS SEEM RIGHT? Y/N  ")
    if r in "Yy":
        return new



def check_extension(folder, fn):
    """Check whether the file extension in the OpenITI file header is known"""
    if  len(fn.split(".")) == 4:
        extension = fn.split(".")[3]
        fn_without_ext = ".".join(fn.split(".")[:3])
        if extension not in ("completed", "mARkdown", "inProgress"):
            print("Extension not recognized:", extension)
            new_ext = input("Write your corrected extension (or press Enter to remove extension): ")
            if not new_ext:
                os.rename(fn, fn_without_ext)
                return fn_without_ext
            else:
                new_fn = fn_without_ext + "." + new_ext.strip()
                r = input("Replace", fn, "with", new_fn, "? Y/n: ")
                if r.lower() != "n":
                    os.rename(fn, new_fn)
                    return new_fn
    return fn


def check_collection(fn):
    """Check whether the collection part of a URI is among the known collections in OpenITI
    
    Args:
        fn (str): filename of the text file

    Returns:
        bool
    """
    try:
        collection = re.split("\d", fn.split(".")[2])[0]
    except:
        return False
    global known_collections
    if collection.startswith(known_collections):
        return True
    else: 
        print("This collection is not known:", collection)
        r = input("Add it to the known collections? Y/n: ")
        if not r.lower() == "n":
            known_collections = known_collections + (collection,)
            print(collection, "added to the known collections")
            return True
    return False

def check_uri(folder, fn):
    """Check whether the filename contains a valid OpenITI URI.

    If the URI is not valid, ask the user to provide a corrected version.
    
    Args:
        folder (str): path to the folder containing the text file
        fn (str): file name of the text file

    
    """
    if re.match(version_uri_regex, fn):
        if check_collection(fn):
            return fn
    
    # Identify the problem in the URI:
    old_fp = os.path.join(folder, fn)
    
    corrected_fn = fn
    if not re.match(author_uri_regex, corrected_fn):
        print("Error in author URI:", corrected_fn)
        print("Please check the author URI has the following structure:")
        print("1. starts with 4 digits")
        print("2. Author name starts with a capital letter")
        print("3. Author name does not contain any special characters")
        print()
        corrected_fn = input("Write your corrected filename here:")
    if not re.match(book_uri_regex, corrected_fn):
        print(book_uri_regex)
        print(re.findall(book_uri_regex, corrected_fn))
        print("Error in book URI:", corrected_fn)
        print("Please check the book title :")
        print("1. It should start with a capital letter")
        print("2. It should not contain any special characters apart from a-z and A-Z")
        print()
        corrected_fn = input("Write your corrected filename here:")
    if not re.match(version_uri_regex, corrected_fn):
        print("Error in version URI:", corrected_fn)
        print("Example of a correct version URI: 0255Jahiz.Hayawan.Shamela00023775-ara1")
        print("Please check whether the last part of the URI consists of:")
        print("1. The name of the collection from which the digital text comes")
        print("2. The ID number of the text in that collection")
        print("3. (separated from the previous by a hyphen) a three-letter language code")
        print("4. A number that refers to the edition used (by default: 1)")
        corrected_fn = input("Write your corrected filename here:")
    
    if re.match(version_uri_regex, fn):
        print("The filename will be changed to", corrected_fn)
        confirm = input("Agreed? Y/n : ")
        if not confirm.lower() == "n":
            # rename the text file:
            new_fp = os.path.join(folder, corrected_fn)
            os.rename(old_fp, new_fp)
            # rename also the yml file, if it exists:
            # TODO: will the URI in the YML file be replaced later?
            old_yml_fp = re.sub("(-([a-z]{3}\d).*", r"\1.yml", old_fp)
            new_yml_fp = re.sub("(-([a-z]{3}\d).*", r"\1.yml", new_fp)  
            try:
                os.rename(old_yml_fp, new_yml_fp)
            except:
                pass
            return corrected_fn
    print("URI still incorrect. Skipping this file")
    return False

def get_all_non_allowed_chars_in_file(fp):
    """Collect a list of unallowed characters in all text files in a file.

    Args:
        fp (str): path to the text file
    
    Returns:
        set
    """
    with open(fp, mode="r", encoding="utf-8") as file:
        text = file.read()
    text = normalize_composites(denoise(text))
    all_chars = "".join(set(text))
    unallowed_chars = re.sub(allowed_chars_regex, "", all_chars)
    return set(unallowed_chars)

def get_all_non_allowed_chars_in_folder(folder):
    """Collect a list of unallowed characters in all text files in the folder.

    Args:
        folder (str): Folder containing the text files
    
    Returns:
        set
    """
    unall_chars = set()
    for fn in os.listdir(folder):
        if fn.endswith((".py", ".yml", ".docx", ".md")):
            continue
        elif fn.startswith("."):
            continue
        fp = os.path.join(folder, fn)
        if not os.path.isdir(fp):
            unall_chars = unall_chars.union(get_all_non_allowed_chars_in_file(fp))
    return unall_chars

def confirm_auto_clean(unall_chars):
    """Ask user to confirm that all unallowed characters may be automatically replaced:
    
    Args:
        unall_chars (set): a set of characters that are not allowed in OpenITI texts
    
    Returns:
        bool
    """
    if len(unall_chars) == 0:
        print("No unallowed characters found in folder.")
        return True

    print("number of unallowed characters:", len(unall_chars))

    print("LISTING ALL CHARACTERS THAT ARE NOT ALLOWED IN OPENITI TEXTS")
    print("AND THAT ARE NOT REMOVED BY THE NORMALIZATION AND DENOISE FUNCTIONS:")

    # print the non-allowed characters in the folder, together with their unicode names:
    unall_chars = "".join(unall_chars)
    not_found = []
    for c in sorted(unall_chars):
        try:
            if repl_dict[c] == "":
                print(c, "\t", unicodedata.name(c), "\t-> (REMOVED)")
            else:
                try:
                    print(c, "\t", unicodedata.name(c), "\t->", repl_dict[c], "\t", unicodedata.name(repl_dict[c]))
                except:
                    print(c, "\t", unicodedata.name(c), "\t->", '"' + repl_dict[c] + '"')
        except:
            try:
                print(c, "\t", unicodedata.name(c), "\t-> ?")
            except:
                not_found.append(c)
    if not_found:
        print("CHARACTERS FOR WHICH NO UNICODE NAME WAS FOUND:")
        for c in not_found:
            print(c)
    print("All of these characters will be automatically replaced with default allowed alternatives")
    print("(if a default replacement for a character has not been defined, you will be asked for advice)")
    r = input("Agree? Y/n: ")
    if r.lower() != "y":
        auto_clean = False
        print("AUTOMATIC REPLACEMENT DECLINED.")
    else:
        auto_clean = True
    return auto_clean

def check_yml_file(yml_fp, yml_type):
    """Check whether a yml file is well-formed and contains the correct URI
    
    Returns:
        bool
    """
    uri = os.path.basename(yml_fp).replace(".yml", "")
    try:
        yml_d = readYML(yml_fp)
    except Exception as e:
        fixed_yml_d = fix_broken_yml(yml_fp)
        if fixed_yml_d:
            with open(yml_fp, mode="w", encoding="utf-8") as file:
                file.write(dicToYML(fixed_yml_d))
            yml_d = fixed_yml_d
        else:
            print("Error in", yml_fp, e)
            return False
    
    # check if the URI in the yml file is the same as in the filename:
    uri_key = "00#{}#URI######:".format(yml_type)
    if yml_d[uri_key] != uri:
        # if not: replace the uri in the yml file with the filename's uri
        print ("replacing URI in yml file:",  yml_d[uri_key], ">", uri)
        yml_d[uri_key] = uri
        with open(yml_fp, mode="w", encoding="utf-8") as file:
            file.write(dicToYML(yml_d))

    return True

def check_yml_files(fp):
    """Check whether yml files accompanying the text file are well-formed.
    
    Args:
        fp (str): path to a text file
    Returns:
        bool
    """
    yml_ok = True
    fp_without_ext, lang, ext = re.findall("(.+?)(-(?:[a-z]{3}\d+)+)(.*)", fp)[0]
    ## version yml file:
    yml_fp = fp_without_ext + lang + ".yml"
    if os.path.exists(yml_fp):
        yml_ok = check_yml_file(yml_fp, "VERS")
    ## book yml file:
    yml_fp = ".".join(fp_without_ext.split(".")[:-1]) + ".yml"
    if os.path.exists(yml_fp):
        yml_ok = check_yml_file(yml_fp, "BOOK")
    # author yml file:
    yml_fp = fp_without_ext.split(".")[0] + ".yml"
    if os.path.exists(yml_fp):
        yml_ok = check_yml_file(yml_fp, "AUTH")
    
    return yml_ok

def main(folder, out_folder, start_date=0, end_date=10000, 
         auto_clean=True, silent=False, do_not_move_regex="[Nn]oorlib", 
         ms_pattern=" *ms[A-Z]?\d+", ms_length=300):
    """Check and clean new text files and move them into the corpus
    
    Args:
        folder (str): path to the folder containing the new files
        out_folder (str): parent folder of the AH folders
        start_date (int): only files written by authors who died after this date will be processed
        end_date (int): only files written by authors who died before this date will be processed
        auto_clean (bool): if True, unallowed characters will be automatically removed
        silent (bool): if True, no confirmation by the user will be asked before auto_cleaning
        do_not_move_regex (str): Regular expression describing all files
            that should not be moved to the out_folder (e.g., Noorlib files)
    
    Returns:
        None
    """
    changed_repos = set()
    header_issues = []
    broken_yml_files = []
    prev_ms = 0

    if auto_clean:
        # Collect a list of unallowed characters in all text files in the folder:
        unall_chars = get_all_non_allowed_chars_in_folder(folder)
        # Ask user to confirm that all these characters may be automatically replaced in all texts:
        if not silent: 
            auto_clean = confirm_auto_clean(unall_chars)
    
    for fn in sorted(os.listdir(folder)):
        # ignore all files that are not text files:
        print(fn)
        if fn.endswith((".yml", ".md", ".py", ".txt", ".docx", ".jpg", ".jpeg", ".png")):
            print("--> aborted: extension")
            continue
        elif fn.startswith("."):
            print("--> aborted: starts with dot")
            continue
        elif not os.path.isfile(os.path.join(folder, fn)):
            print("--> aborted: not a file")
            continue
        print(fn)

        # check filename and extension:
        fn = check_uri(folder, fn)
        if not fn:
            continue  # don't process this file if no correct filename was provided
        fn = check_extension(folder, fn)

        # check if the date of the author's death falls in the desired date range
        try:
            date = int(fn[:4])
            if not start_date < date < end_date:
                continue  # do not process this file
        except Exception as e:
            print("Error processing", fn, ":", e)
            print("Does the filename start with 4 digits?")
            continue  # do not process this file: filename not correct

        # Check the contents of the text file:
        fp = os.path.join(folder, fn)
        with open(fp, mode="r", encoding="utf-8-sig") as file:
            text = file.read()
           
            # Check whether the metadata header is present:
            header, text = check_meta_header(text)
            if not header:
                print(fn, ": problem with metadata header")
                header_issues.append(fn)
                continue  # do not process this file: problem with metadata header
            
            # Remove unallowed characters from the main body of the text:
            text = clean(text, fn, auto_clean)

            # Add mARkdown paragraph marks if necessary:
            text = check_paragraph_marks(text, fn)

            # final cleaning:
            text = post_process(text)

            # remove any existing milestone IDs and create new ones:
            text = re.sub(ms_pattern, "", text)
            text = re.sub(" *Milestone\d+", "", text)
            text, prev_ms = milestone(text, fn, prev_ms=prev_ms, ms_length=ms_length)
            if prev_ms is None:
                continue  # do not process this file: something went wrong with milestoning!

            # re-assemble the header and text:
            text = header + "#META#Header#End#" + text
        
        # DEBUG:
        # # write the changes to the text file:
        # with open(fp, mode="w", encoding="utf-8") as file:
        #    file.write(text)

 
        # check whether any related yml files are well-formed:
        yml_ok = check_yml_files(fp)
        if not yml_ok:
            broken_yml_files.append(fp)
            continue  # skip this text file because its yml files are not ok!


        # Move the text file to the corpus folder
        # (except files that match a specified regex: do_not_move_regex)
        # If a text file has an accompanying yml file, it will be moved as well;
        # if not, a blank yml file will be created in the destination repo.
        if re.findall(do_not_move_regex, fn):
            print(fn, "cleaned but not moved to folder: on ignore list")
        elif os.path.isfile(fp):
            # DEBUG:
            # initialize_new_text(fp, out_folder, execute=True)

            # store repo to a list of all repos to which new texts were added:
            y = int(fn[:4])
            if y % 25:
                repo = "{:04d}AH".format((int(y/25) + 1)*25)
            else:
                repo = "{:04d}AH".format(y)
            changed_repos.add(os.path.join(out_folder, repo))

    if changed_repos:
        print("---------------")
        print("List of all changed repos:")
        for repo in sorted(changed_repos):
            print(repo)

    if header_issues:
        print("---------------")
        print("List of all text files with problems in the OpenITI header:")
        for fp in header_issues:
            print(fp)

    if broken_yml_files:
        print("---------------")
        print("List of all text files with broken yml files:")
        for fp in broken_yml_files:
            print(fp)



if __name__ == "__main__":
    main(folder=r"D:\AKU\OpenITI\barzakh", out_folder=r"D:\AKU\OpenITI\25Y_repos")