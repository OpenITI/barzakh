from openiti.helper.ara import *
import unicodedata
import os
import re
import textwrap

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
, 	 COMMA
= 	 EQUALS SIGN
? 	 QUESTION MARK
"""
allowed_chars = [x.split("\t")[0] for x in allowed_chars.splitlines()]
allowed_chars = re.compile("[{}]+".format("".join(allowed_chars)))

remove = """\
‌	ZERO WIDTH NON-JOINER
‍	ZERO WIDTH JOINER
"""
remove = [x.split("\t")[0] for x in remove.splitlines()]
remove = re.compile("[{}]+".format("".join(remove)))

repl_dict = {"…": "...", "ک": "ك", "ی": "ي", }

def clean(text):
    text = deNoise(text)
    text = re.sub(remove, "", text)
    #text = re.sub("﻿", "", text) # remove zero width no-break space
    all_chars = "".join(set(text))
    filtered_chars = re.sub(allowed_chars, "", all_chars)
    filtered_chars = re.sub("[0-9a-zA-Z \n\t\[\]]+", "", filtered_chars)
    not_found = []
    for c in sorted(filtered_chars):
        try:
            print(c, "\t", unicodedata.name(c))
        except:
            not_found.append(c)
        if c not in not_found: 
            print(re.findall("[^%s]{,10}%s[^%s]{,10}"%(c,c,c), text))
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
    return text

def rewrap(text, maxlength=72):
    text = re.sub("(### \|+.+[\r\n]+)([^#P])", r"\1# \2", text)
    text = re.sub("[\r\n]+~~", " ", text)
    text = re.sub("[\r\n]+([^P#])", r" \1", text)
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

for fn in os.listdir("."):
    if fn.endswith(("-ara1", ".completed")):
        print(fn)
        with open(fn, mode="r", encoding="utf-8-sig") as file:
            text = file.read()
            text = clean(text)
            text = rewrap(text, 72)

        if text:
            with open(fn, mode="w", encoding="utf-8-sig") as file:
                file.write(text)
        else:
            print("rewriting file", fn, "aborted")

        

