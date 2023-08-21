from openiti.helper.ara import *
import unicodedata
import os
import re
import textwrap
from shutil import copyfile

# Whitelist of characters that are allowed in OpenITI texts:

allowed_chars = """\
ء	ARABIC LETTER HAMZA
آ	ARABIC LETTER ALEF WITH MADDA ABOVE
أ	ARABIC LETTER ALEF WITH HAMZA ABOVE
ؤ	ARABIC LETTER WAW WITH HAMZA ABOVE
إ	ARABIC LETTER ALEF WITH HAMZA BELOW
ئ	ARABIC LETTER YEH WITH HAMZA ABOVE
ا	ARABIC LETTER ALEF
ب	ARABIC LETTER BEH
ة	ARABIC LETTER TEH MARBUTA
ت	ARABIC LETTER TEH
ث	ARABIC LETTER THEH
ج	ARABIC LETTER JEEM
ح	ARABIC LETTER HAH
خ	ARABIC LETTER KHAH
د	ARABIC LETTER DAL
ذ	ARABIC LETTER THAL
ر	ARABIC LETTER REH
ز	ARABIC LETTER ZAIN
س	ARABIC LETTER SEEN
ش	ARABIC LETTER SHEEN
ص	ARABIC LETTER SAD
ض	ARABIC LETTER DAD
ط	ARABIC LETTER TAH
ظ	ARABIC LETTER ZAH
ع	ARABIC LETTER AIN
غ	ARABIC LETTER GHAIN
ف	ARABIC LETTER FEH
ق	ARABIC LETTER QAF
ك	ARABIC LETTER KAF
ل	ARABIC LETTER LAM
م	ARABIC LETTER MEEM
ن	ARABIC LETTER NOON
ه	ARABIC LETTER HEH
و	ARABIC LETTER WAW
ى	ARABIC LETTER ALEF MAKSURA
ي	ARABIC LETTER YEH
٠	ARABIC-INDIC DIGIT ZERO
١	ARABIC-INDIC DIGIT ONE
٢	ARABIC-INDIC DIGIT TWO
٣	ARABIC-INDIC DIGIT THREE
٤	ARABIC-INDIC DIGIT FOUR
٥	ARABIC-INDIC DIGIT FIVE
٦	ARABIC-INDIC DIGIT SIX
٧	ARABIC-INDIC DIGIT SEVEN
٨	ARABIC-INDIC DIGIT EIGHT
٩	ARABIC-INDIC DIGIT NINE
ٹ	ARABIC LETTER TTEH
پ	ARABIC LETTER PEH
چ	ARABIC LETTER TCHEH
ڈ	ARABIC LETTER DDAL
ڑ	ARABIC LETTER RREH
ژ	ARABIC LETTER JEH
ک	ARABIC LETTER KEHEH
ݣ	ARABIC LETTER KEHEH WITH THREE DOTS ABOVE
ڭ	ARABIC LETTER NG
گ	ARABIC LETTER GAF
ں	ARABIC LETTER NOON GHUNNA
ۀ	ARABIC LETTER HEH WITH YEH ABOVE
ہ	ARABIC LETTER HEH GOAL
ۂ	ARABIC LETTER HEH GOAL WITH HAMZA ABOVE
ی	ARABIC LETTER FARSI YEH
ے	ARABIC LETTER YEH BARREE
ۓ	ARABIC LETTER YEH BARREE WITH HAMZA ABOVE
ھ	ARABIC LETTER HEH DOACHASHMEE
ە	ARABIC LETTER AE
‌	ZERO WIDTH NON-JOINER
ٔ	ARABIC HAMZA ABOVE (needed for the Farsi izafeh)
#	NUMBER SIGN
%	PERCENT SIGN
(	LEFT PARENTHESIS
)	RIGHT PARENTHESIS
.	FULL STOP
/	SOLIDUS
0	DIGIT ZERO
1	DIGIT ONE
2	DIGIT TWO
3	DIGIT THREE
4	DIGIT FOUR
5	DIGIT FIVE
7	DIGIT SEVEN
8	DIGIT EIGHT
9	DIGIT NINE
:	COLON
|	VERTICAL LINE
~	TILDE
؟	ARABIC QUESTION MARK
،	ARABIC COMMA
!	EXCLAMATION MARK
$	DOLLAR SIGN
*	ASTERISK
-	HYPHEN-MINUS
_	LOW LINE (i.e., underscore)
«	LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
»	RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
؛	ARABIC SEMICOLON
!	EXCLAMATION MARK
"	QUOTATION MARK
,	COMMA
=	EQUALS SIGN
?	QUESTION MARK
“	LEFT DOUBLE QUOTATION MARK
”	RIGHT DOUBLE QUOTATION MARK
’	RIGHT SINGLE QUOTATION MARK
¶	PILCROW SIGN
¬	NOT SIGN
•	BULLET
<	LESS-THAN SIGN
>	GREATER-THAN SIGN
{	LEFT CURLY BRACKET
}	RIGHT CURLY BRACKET
+	PLUS SIGN
;	SEMICOLON
@	COMMERCIAL AT
ְ	HEBREW POINT SHEVA
ֳ	HEBREW POINT HATAF QAMATS
ִ	HEBREW POINT HIRIQ
ֵ	HEBREW POINT TSERE
ֶ	HEBREW POINT SEGOL
ַ	HEBREW POINT PATAH
ָ	HEBREW POINT QAMATS
ֹ	HEBREW POINT HOLAM
ּ	HEBREW POINT DAGESH OR MAPIQ
א	HEBREW LETTER ALEF
ב	HEBREW LETTER BET
ג	HEBREW LETTER GIMEL
ד	HEBREW LETTER DALET
ה	HEBREW LETTER HE
ו	HEBREW LETTER VAV
ז	HEBREW LETTER ZAYIN
ח	HEBREW LETTER HET
ט	HEBREW LETTER TET
י	HEBREW LETTER YOD
ך	HEBREW LETTER FINAL KAF
כ	HEBREW LETTER KAF
ל	HEBREW LETTER LAMED
ם	HEBREW LETTER FINAL MEM
מ	HEBREW LETTER MEM
ן	HEBREW LETTER FINAL NUN
נ	HEBREW LETTER NUN
ס	HEBREW LETTER SAMEKH
ע	HEBREW LETTER AYIN
ף	HEBREW LETTER FINAL PE
פ	HEBREW LETTER PE
ץ	HEBREW LETTER FINAL TSADI
צ	HEBREW LETTER TSADI
ק	HEBREW LETTER QOF
ר	HEBREW LETTER RESH
ש	HEBREW LETTER SHIN
ת	HEBREW LETTER TAV
І	CYRILLIC CAPITAL LETTER BYELORUSSIAN-UKRAINIAN I
А	CYRILLIC CAPITAL LETTER A
Б	CYRILLIC CAPITAL LETTER BE
В	CYRILLIC CAPITAL LETTER VE
Г	CYRILLIC CAPITAL LETTER GHE
Д	CYRILLIC CAPITAL LETTER DE
Е	CYRILLIC CAPITAL LETTER IE
Ж	CYRILLIC CAPITAL LETTER ZHE
З	CYRILLIC CAPITAL LETTER ZE
И	CYRILLIC CAPITAL LETTER I
Й	CYRILLIC CAPITAL LETTER SHORT I
К	CYRILLIC CAPITAL LETTER KA
Л	CYRILLIC CAPITAL LETTER EL
М	CYRILLIC CAPITAL LETTER EM
Н	CYRILLIC CAPITAL LETTER EN
О	CYRILLIC CAPITAL LETTER O
П	CYRILLIC CAPITAL LETTER PE
Р	CYRILLIC CAPITAL LETTER ER
С	CYRILLIC CAPITAL LETTER ES
Т	CYRILLIC CAPITAL LETTER TE
У	CYRILLIC CAPITAL LETTER U
Ф	CYRILLIC CAPITAL LETTER EF
Х	CYRILLIC CAPITAL LETTER HA
Ц	CYRILLIC CAPITAL LETTER TSE
Ч	CYRILLIC CAPITAL LETTER CHE
Ш	CYRILLIC CAPITAL LETTER SHA
Щ	CYRILLIC CAPITAL LETTER SHCHA
Ъ	CYRILLIC CAPITAL LETTER HARD SIGN
Ы	CYRILLIC CAPITAL LETTER YERU
Ь	CYRILLIC CAPITAL LETTER SOFT SIGN
Э	CYRILLIC CAPITAL LETTER E
Ю	CYRILLIC CAPITAL LETTER YU
Я	CYRILLIC CAPITAL LETTER YA
а	CYRILLIC SMALL LETTER A
б	CYRILLIC SMALL LETTER BE
в	CYRILLIC SMALL LETTER VE
г	CYRILLIC SMALL LETTER GHE
д	CYRILLIC SMALL LETTER DE
е	CYRILLIC SMALL LETTER IE
ж	CYRILLIC SMALL LETTER ZHE
з	CYRILLIC SMALL LETTER ZE
и	CYRILLIC SMALL LETTER I
й	CYRILLIC SMALL LETTER SHORT I
к	CYRILLIC SMALL LETTER KA
л	CYRILLIC SMALL LETTER EL
м	CYRILLIC SMALL LETTER EM
н	CYRILLIC SMALL LETTER EN
о	CYRILLIC SMALL LETTER O
п	CYRILLIC SMALL LETTER PE
р	CYRILLIC SMALL LETTER ER
с	CYRILLIC SMALL LETTER ES
т	CYRILLIC SMALL LETTER TE
у	CYRILLIC SMALL LETTER U
ф	CYRILLIC SMALL LETTER EF
х	CYRILLIC SMALL LETTER HA
ц	CYRILLIC SMALL LETTER TSE
ч	CYRILLIC SMALL LETTER CHE
ш	CYRILLIC SMALL LETTER SHA
щ	CYRILLIC SMALL LETTER SHCHA
ъ	CYRILLIC SMALL LETTER HARD SIGN
ы	CYRILLIC SMALL LETTER YERU
ь	CYRILLIC SMALL LETTER SOFT SIGN
э	CYRILLIC SMALL LETTER E
ю	CYRILLIC SMALL LETTER YU
я	CYRILLIC SMALL LETTER YA
і	CYRILLIC SMALL LETTER BYELORUSSIAN-UKRAINIAN I
Ѣ	CYRILLIC CAPITAL LETTER YAT
ѣ	CYRILLIC SMALL LETTER YAT
Ѳ	CYRILLIC CAPITAL LETTER FITA
"""
allowed_chars = [x.split("\t")[0] for x in allowed_chars.splitlines()]
allowed_chars = [c for c in allowed_chars if c not in ("-", ".")]

# In addition to the above characters, also include Latin script, whitespace and punctuation:
transcription_chars = "0-9a-zA-ZāĀēĒṭṬṯṮūŪīĪİıōŌṣṢšŠḍḌḏḎǧǦġĠḫḪḳḲẓẒžŽčČçÇñÑãÃáÁàÀäÄéÉèÈêÊëËïÏîÎôÔóÓòÒōÕöÖüÜûÛúÚùÙʿʾ' "
escaped_chars = r"\"\n\t\[\]\.\-\\"

# build a regex to match all allowed characters (and all those that are not allowed):
allowed_chars_regex = re.compile(r"[{}{}{}]+".format("".join(allowed_chars), transcription_chars, escaped_chars))
unwanted_chars_regex = re.compile(r"[^{}{}{}]+".format("".join(allowed_chars), transcription_chars, escaped_chars))


# Create replacement tuples:

# first, create some variables for a couple of special characters: 

HAMZA_ABOVE = "ٔ"
HAMZA_BELOW = "ٕ"
MADDAH_ABOVE = "ٓ"
SMALL_MADDAH = "ۤ"
zw = """\
‌	ZERO WIDTH NON-JOINER
‍	ZERO WIDTH JOINER
"""
ZWNJ = [x.split("\t")[0] for x in zw.splitlines()][0]
ZWJ  = [x.split("\t")[0] for x in zw.splitlines()][1]

# then, build replacement tuples for characters that should be replaced in any text:

repl_dict = {"…": "...",
             "٭": "*",   # ARABIC FIVE POINTED STAR
             "ک": "ك",   # Persian glyphs for Arabic letters
             "ی": "ي",
             "۰": "٠",   # EXTENDED ARABIC-INDIC DIGITs
             "۱": "١",
             "۲": "٢", 
             "۳": "٣",
             "۴": "٤",
             "۵": "٥",
             "۶": "٦",
             "۷": "٧",
             "۸": "٨",
             "۹": "٩",
             "–": "-",   # EN DASH
             "—": "-",   # EM DASH
             "⁄": "/",   # FRACTION SLASH
             "ٱ": "ا",   # U+0671 : ARABIC LETTER ALEF WASLA
             "اۤ": "آ",   # ARABIC LETTER ALEF + ARABIC SMALL HIGH MADDA
             "ۤ": "",     # ARABIC SMALL HIGH MADDA
             "أٓ": "آ"}

repl_tup = [
    ("…", "..."),
    ("٭", "*"),   # ARABIC FIVE POINTED STAR
    ("∗", "*"),   # ASTERISK OPERATOR
    ("❊", "*"),   # EIGHT TEARDROP-SPOKED PROPELLER ASTERISK
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
    ("ا"+MADDAH_ABOVE, "آ"),
    #(MADDAH_ABOVE+"ا", "آ"),
    ("ا"+SMALL_MADDAH, "آ"),
    (SMALL_MADDAH+"ا", "آ"),
    ("ا"+HAMZA_BELOW, "إ"),
    (HAMZA_BELOW+"ا", "إ"),
    ("ا"+HAMZA_ABOVE, "أ"),
    #(HAMZA_ABOVE+"ا", "أ"),
    ("و"+HAMZA_ABOVE, "ؤ"),
    #(HAMZA_ABOVE+"و", "ؤ"),
    ("ى"+HAMZA_ABOVE, "ئ"),
    #(HAMZA_ABOVE+"ى", "ئ"),
    ("أ"+MADDAH_ABOVE, "آ"),
    #(MADDAH_ABOVE+"أ", "آ"),
    ("أ"+SMALL_MADDAH, "آ"),
    (SMALL_MADDAH+"أ", "آ"),
    ("﻿", ""),   # ZERO WIDTH NO-BREAK SPACE [ZWNBSP] (alias BYTE ORDER MARK [BOM])
    (HAMZA_ABOVE, ""),
    (MADDAH_ABOVE, ""),
    (SMALL_MADDAH, ""),
    (HAMZA_BELOW, "")
    ]

# finally, replace some glyphs in a specific language only:
# (based partly on https://scripts.sil.org/cms/scripts/render_download.php?format=file&media_id=arabicletterusagenotes&filename=ArabicLetterUsageNotes.pdf)

repl_tup_ara = [    # Persian/Urdu glyphs for Arabic letters, normalized in Arabic texts:
    ("ک", "ك"),   
    ("ی", "ي"),
    ("ے", "ي"),
    ("ۓ", "ئ"),
    ("ڭ", "ك"),
    ("ں", "ن"),
    ("ھ", "ه"),     # ARABIC LETTER HEH DOACHASHMEE
    ("ہ", "ه"),     # ARABIC LETTER HEH GOAL
    ("ۂ", "ه"),     # ARABIC LETTER HEH GOAL WITH HAMZA ABOVE
    ("ۀ", "ه"),     # ARABIC LETTER HEH WITH YEH ABOVE
    (ZWNJ, ""),     # ZERO WIDTH NON JOINER
    (HAMZA_ABOVE, ""),
    ]

repl_tup_per = [    # Arabic glyphs not used for Persian:
    ("ك", "ک"),   
    ("ي", "ی"),
    ("ے", "ی"),
    ("ى", "ی"),     # Alif maksura
    ("ۓ", "ئ"),
    ("ڭ", "گ"),
    ("ں", "ن"),
    ("ھ", "ه"),     # ARABIC LETTER HEH DOACHASHMEE
    ("ہ", "ه"),     # ARABIC LETTER HEH GOAL
    ("﻿", ZWNJ),     # ZERO WIDTH NO-BREAK SPACE [ZWNBSP] (alias BYTE ORDER MARK [BOM])
    ("ۂ"+ZWNJ+"?", "ه"+HAMZA_ABOVE+ZWNJ), # ARABIC LETTER HEH GOAL WITH HAMZA ABOVE
    ("ۀ"+ZWNJ+"?", "ه"+HAMZA_ABOVE+ZWNJ), # ARABIC LETTER HEH WITH YEH ABOVE
    ]

repl_tup_urd = [
    ("ك", "ک"),
    ("ي", "ی"),
    ("ى", "ی"),     # Alif maksura
    ]


def add_paragraph_marks(text, keep_line_endings=True, maxlength=72):
    """Add paragraph marks (hashtags and tildas) to one file.

    Args:
        text (str): text as string
        keep_line_endings (bool): if True, line endings in the original file
            will be kept; if False, long lines will be broken into
            shorter lines.
    """

    # add # after line that ends with full stop, question and exclamation marks:
    ptrn = r"([.؟!] *[\r\n]+(?:PageV\w{2}P\d+[abAB]?[\r\n]+)?)([^\r\n#P])"
    text = re.sub(ptrn, r"\1# \2", text)

    # add # after section titles (but not before page numbers and sub-titles)
    ptrn = r"(### .+[\r\n]+(?:PageV\w{2}P\d+[\r\n]+)?)([^\r\n#P])"
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
        text = re.sub(ptrn, r"\1 \2 ", text)
        # Add paragraph signs before every new line:
        ptrn = r"([\r\n]+)([^\r\n#P\s])"
        text = re.sub(ptrn, r"\1# \2", text)
        # break long lines into shorter lines:
        new_text = wrap(text, maxlength)

    new_text = re.sub("~~#", "#", new_text)
    new_text = re.sub(r"~~([^\n]+%~%)", r"# \1", new_text)
    new_text = re.sub(r"~~\.\./", "../", new_text)

    return new_text

def wrap(text, max_length=72):
    wrapped = []
    for line in re.split("([\r\n]+)", text):
        if line.startswith(("###", "\r", "\n")):
            wrapped.append(line)
        else:
            lines = textwrap.wrap(line, max_length, break_long_words=False)
            wrapped.append("\n~~".join(lines))

    return "".join(wrapped)


def get_all_non_allowed_chars_in_file(fp, print_output=False):
    with open(fp, mode="r", encoding="utf-8") as file:
        text = file.read()
    text = normalize_composites(denoise(text))
    all_chars = "".join(set(text))
    filtered_chars = re.sub(allowed_chars_regex, "", all_chars)
    return filtered_chars

def get_all_non_allowed_chars_in_folder(folder):
    all_chars = set()
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if os.path.isfile(fp) and not fn.endswith((".py", ".yml", ".docx", ".md")):
            print(fn)
            all_chars = all_chars.union(set(get_all_non_allowed_chars_in_file(fp)))
            print("Subtotal: number of unallowed characters:", len(all_chars))
    # print the non-allowed characters in the folder:
    all_chars = "".join(all_chars)
    not_found = []
    for c in sorted(all_chars):
        try:
            print(c, "\t", unicodedata.name(c))
        except:
            not_found.append(c)
    if not_found:
        print("NOT FOUND:")
        for c in not_found:
            print(c)


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

def clean(text, fn, auto=False):
    print(fn)
    # check presence of metadata header:
    if not text.strip().startswith("######OpenITI#"):
        if not "#META#Header#End#" in text:
            text = "######OpenITI#\n\n#META#Header#End#\n"+text.strip()
        else:
            input("HEADER NOT FOUND! Continue?")
    header, text = text.split("#META#Header#End#")
    if not header:
        input("HEADER NOT FOUND! Continue?")

##    editor = re.findall("### \|EDITOR\|.+?###", text, flags=re.DOTALL)
##    if editor:
##        editor = editor[0]
##        print("EDITORIAL:")
##        print(editor)
##        print("END OF EDITORIAL")
##        text = re.sub("### \|EDITOR\|.+?###", "INSERT_EDITOR", text, 1, flags=re.DOTALL)
##    else:
##        editor = ""

    # clean text from unwanted characters:
    text = deNoise(text)
    text = normalize_composites(text)
    #text = re.sub(remove, "", text)
    #text = re.sub("أٓ", "آ", text)

    # replace all patterns for which an auto replacement has been defined:
    print("Going through general replacement patterns...")
    for pattern, repl in repl_tup:
        text = ask_replace_permission(text, pattern, repl, auto)
    if re.findall("-(?:[a-z]{3})*ara", fn):
        print("Going through replacement patterns for Arabic text...")
        for pattern, repl in repl_tup_ara:
            print([pattern])
            text = ask_replace_permission(text, pattern, repl, auto)
    if re.findall("-(?:[a-z]{3})*per", fn):
        print("Going through replacement patterns for Persian text...")
        for pattern, repl in repl_tup_per:
            text = ask_replace_permission(text, pattern, repl, auto)
    if re.findall("-(?:[a-z]{3})*urd", fn):
        print("Going through replacement patterns for Urdu text...")
        for pattern, repl in repl_tup_urd:
            text = ask_replace_permission(text, pattern, repl, auto)

    # replace all remaining unwanted characters:
    if auto:
        text = re.sub(unwanted_chars_regex, "", text)
    else:       
        all_chars = "".join(set(text))
        filtered_chars = re.sub(allowed_chars_regex, "", all_chars)
        #filtered_chars = re.sub("[0-9a-zA-ZāĀēĒṭṬṯṮūŪīĪİıōŌṣṢšŠḍḌḏḎǧǦġĠḫḪḳḲẓẒčČçÇñÑãÃáÁàÀäÄéÉèÈêÊëËïÏîÎôÔóÓòÒōÕöÖüÜûÛúÚùÙʿʾ' \"\n\t\[\]]+", "", filtered_chars)
        print("REMAINING SUSPICIOUS CHARACTERS AFTER FIRST CLEANING:", len(filtered_chars))
        not_found = []
        for c in sorted(filtered_chars):
            try:
                print(c, "\t", unicodedata.name(c))
            except:
                not_found.append(c)
            if c not in not_found: 
                for x in re.findall("[^%s]{,20}%s[^%s]{,20}"%(c,c,c), text)[:10]:
                    print(x)
                    print("-"*30)
                print("({} times in text)".format(len(re.findall(c, text))))
                resp = input("Do you want to replace all? Y/N  ")
                if resp in "Yy":
                    if c in repl_dict:
                        text = re.sub(c, repl_dict[c], text)
                    else:
                        print("What character do you want to replace it by? ")
                        r = input("(None if you don't want to replace)  ")
                        if r != "None":
                            text = re.sub(c, r, text)
                    print("replaced", unicodedata.name(c))
        if not_found:
            print("not found:", not_found)
        #return text

    # add paragraph marks:
    if not "~~" in text:
        if re.findall("eScr|Kraken|Tess|GVDB", fn):
            text = add_paragraph_marks(text, keep_line_endings=True)
        else:
            text = add_paragraph_marks(text, keep_line_endings=False)
##    if editor:
##        text = re.sub("INSERT_EDITOR", editor, text)

    # final cleaning:
    text = re.sub(" ###", "\n\n###", text)
    #text = re.sub(r"(#META#Header#End#)~~[ \r\n]+~~", r"\1\n\n# ", text)
    #text = re.sub("(#META#Header#End#)~~[ \r\n]+", r"\1\n\n", text)
    text = re.sub(r"\A~~[ \r\n]+~~", r"\n\n# ", text)
    text = re.sub(r"\A~~[ \r\n]+", r"\n\n", text)
    text = re.sub(r"[\r\n]+~~ *(?:[\r\n]+|\Z)", "\n", text)
    text = re.sub("(?<=# |~~) *ا\s+| +ا *(?=[\r\n])", "", text) # fix leading and trailing alif issue (OCR)
    text = re.sub("~~ ", "~~", text)
    text = re.sub(r"\b([وفبلك]*(?:ا?ل)?)شئ\b", r"\1شيء", text)  # al-shay'



    return header + "#META#Header#End#" + text

def rewrap(text, maxlength=72):
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




AUTO_CLEAN = True
folder = "."

if AUTO_CLEAN:
    print("LISTING ALL CHARACTERS THAT ARE NOT ALLOWED IN OPENITI TEXTS")
    print("AND THAT ARE NOT REMOVED BY THE NORMALIZATION AND DENOISE FUNCTIONS:")
    get_all_non_allowed_chars_in_folder(folder)
    r = input("All of these characters will be deleted or replaced. Agree? Y/N: ")
    if r.lower() != "y":
        AUTO_CLEAN = False
        print("AUTOMATIC REPLACEMENT DECLINED.")

start = 0
for fn in os.listdir(folder):
    fp = os.path.join(folder, fn)
    #if fn.endswith(("-ara1", ".completed")):
    d = re.findall("^\d{4}", fn)
    if d and not fn.endswith("yml") and int(d[0]) >= start:
        if fn.endswith(".txt"):
            copyfile(fn, fn[:-4])
            os.remove(fn)
            print("changed filename:", fn, ">", fn[:-4])
            fn = fn[:-4]
        print(fn)
        with open(fp, mode="r", encoding="utf-8-sig") as file:
            text = file.read()
            text = clean(text, fn, AUTO_CLEAN)
##            text = re.sub(" ###", "\n\n###", text)
##            text = re.sub("(#META#Header#End#)~~[\r\n]+~~", r"\1\n\n# ", text)
##            text = re.sub("(#META#Header#End#)~~[\r\n]+", r"\1\n\n", text)
##            text = re.sub(r"[\r\n]+~~ *(?:[\r\n]+|\Z)", "\n", text)
##            text = re.sub("(?<=# |~~) *ا +| +ا *(?=[\r\n])", "", text)
##            text = re.sub("~~ ", "~~", text)
            #text = rewrap(text, 72)
        if text:
            with open(fp, mode="w", encoding="utf-8-sig") as file:
                file.write(text.strip())
        else:
            print("rewriting file", fn, "aborted")

        # check yml file:
        if fn.endswith(("inProgress", "completed", "mARkdown")):
            yml_fn = os.path.splitext(fn)[0] + ".yml"
        else:
            yml_fn = fn + ".yml"
        print("**YML: "+yml_fn)
        yml_fp = os.path.join(folder, yml_fn)
        with open(yml_fp, mode="r", encoding="utf-8") as file:
            yml_str = file.read()
        if not yml_fn[:-4] in yml_str:
            if "00#VERS#URI######:" in yml_str:
                yml_str = re.sub("00#VERS#URI######:.*", "00#VERS#URI######: "+yml_fn[:-4], yml_str)
                with open(yml_fp, mode="w", encoding="utf-8") as file:
                    file.write(yml_str)
            else:
                print(yml_str)


"""
0363QadiNucman.Idah.EShia0027411-ara1
̈	COMBINING DIAERESIS   
� 	 REPLACEMENT CHARACTER
"""
