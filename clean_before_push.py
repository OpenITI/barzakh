from openiti.helper.ara import *
import unicodedata
import os
import re
import textwrap
from shutil import copyfile

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
¶	PILCROW SIGN
¬	NOT SIGN
•	BULLET
"""
allowed_chars = [x.split("\t")[0] for x in allowed_chars.splitlines()]
allowed_chars = re.compile("[{}]+".format("".join(allowed_chars)))

remove = """\
‌	ZERO WIDTH NON-JOINER
‍	ZERO WIDTH JOINER
"""
remove = [x.split("\t")[0] for x in remove.splitlines()]
remove = re.compile("[{}]+".format("".join(remove)))

repl_dict = {"…": "...", "ک": "ك", "ی": "ي", "۰": "٠", "۱": "١", "۳": "٣",
             "۹": "٩", "–": "-", "—": "-", "⁄": "/", "ٱ": "ا", "اۤ": "آ",
             "ۤ": "", "أٓ": "آ"}

def add_paragraph_marks(text, keep_line_endings=True, maxlength=72):
    """Add paragraph marks (hashtags and tildas) to one file.

    Args:
        text (str): text as string
        keep_line_endings (bool): if True, line endings in the original file
            will be kept; if False, long lines will be broken into
            shorter lines.
    """

    # add # after line that ends with full stop, question and exclamation marks:
    ptrn = r"([.؟!] *[\r\n]+(?:PageV\w{2}P\d+[abAB]?[\r\n]+)?)([^\r\n#P\Z])"
    text = re.sub(ptrn, r"\1# \2", text)

    # add # after section titles (but not before page numbers and sub-titles)
    ptrn = r"(### .+[\r\n]+(?:PageV\w{2}P\d+[\r\n]+)?)([^\r\n#P\Z])"
    text = re.sub(ptrn, r"\1# \2", text)

    if keep_line_endings:
        #  add the tildas for continued lines:
        new_text = ""
        for line in re.split(r"([\r\n]+)", text):
            if not line.startswith(("P", "#", "~~")) \
               and not re.match(r"([\r\n]+)", line):
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

def clean(text, fn):
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
    text = re.sub(remove, "", text)
    text = re.sub("أٓ", "آ", text)

    all_chars = "".join(set(text))
    filtered_chars = re.sub(allowed_chars, "", all_chars)
    filtered_chars = re.sub("[0-9a-zA-Zū'ʿ \n\t\[\]]+", "", filtered_chars)
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
    text = re.sub("(#META#Header#End#)~~[\r\n]+~~", r"\1\n\n# ", text)
    text = re.sub("(#META#Header#End#)~~[\r\n]+", r"\1\n\n", text)
    text = re.sub(r"[\r\n]+~~ *(?:[\r\n]+|\Z)", "\n", text)
    text = re.sub("(?<=# |~~) *ا +| +ا *(?=[\r\n])", "", text)
    text = re.sub("~~ ", "~~", text)


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

start = 0
for fn in os.listdir("."):
    #if fn.endswith(("-ara1", ".completed")):
    d = re.findall("^\d{4}", fn)
    if d and not fn.endswith("yml") and int(d[0]) >= start:
        if fn.endswith(".txt"):
            copyfile(fn, fn[:-4])
            os.remove(fn)
            print("changed filename:", fn, ">", fn[:-4])
            fn = fn[:-4]
        print(fn)
        with open(fn, mode="r", encoding="utf-8-sig") as file:
            text = file.read()
            text = clean(text, fn)
##            text = re.sub(" ###", "\n\n###", text)
##            text = re.sub("(#META#Header#End#)~~[\r\n]+~~", r"\1\n\n# ", text)
##            text = re.sub("(#META#Header#End#)~~[\r\n]+", r"\1\n\n", text)
##            text = re.sub(r"[\r\n]+~~ *(?:[\r\n]+|\Z)", "\n", text)
##            text = re.sub("(?<=# |~~) *ا +| +ا *(?=[\r\n])", "", text)
##            text = re.sub("~~ ", "~~", text)
            #text = rewrap(text, 72)
        if text:
            with open(fn, mode="w", encoding="utf-8-sig") as file:
                file.write(text.strip())
        else:
            print("rewriting file", fn, "aborted")

        # check yml file:
        if fn.endswith(("inProgress", "completed", "mARkdown")):
            yml_fn = os.path.splitext(fn)[0] + ".yml"
        else:
            yml_fn = fn + ".yml"
        print("**YML: "+yml_fn)
        with open(yml_fn, mode="r", encoding="utf-8") as file:
            yml_str = file.read()
        if not yml_fn[:-4] in yml_str:
            if "00#VERS#URI######:" in yml_str:
                yml_str = re.sub("00#VERS#URI######:.*", "00#VERS#URI######: "+yml_fn[:-4], yml_str)
                with open(yml_fn, mode="w", encoding="utf-8") as file:
                    file.write(yml_str)
            else:
                print(yml_str)


"""
0363QadiNucman.Idah.EShia0027411-ara1
̈ 	 COMBINING DIAERESIS   
� 	 REPLACEMENT CHARACTER
"""
