from openiti.helper.ara import *
import unicodedata
import os
import re



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
<	LESS-THAN SIGN
>	GREATER-THAN SIGN
{	LEFT CURLY BRACKET
}	RIGHT CURLY BRACKET
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
"""
allowed_chars = [x.split("\t")[0] for x in allowed_chars.splitlines()]
allowed_chars = [c for c in allowed_chars if c not in ("-", ".")]
allowed_chars += ["\.", "\-"]
allowed_chars = re.compile("[{}]+".format("".join(allowed_chars)))

def get_all_non_allowed_chars_in_file(fp, print_output=False):
    with open(fp, mode="r", encoding="utf-8") as file:
        text = file.read()
    text = normalize_composites(denoise(text))
    all_chars = "".join(set(text))
    filtered_chars = re.sub(allowed_chars, "", all_chars)
    filtered_chars = re.sub("[0-9a-zA-ZāĀēĒṭṬṯṮūŪīĪİıōŌṣṢšŠḍḌḏḎǧǦġĠḫḪḳḲẓẒčČñʿʾ' \"\n\t\[\]]+", "", filtered_chars)
    return filtered_chars

def get_all_non_allowed_chars_in_folder(folder):
    all_chars = set()
    for fn in os.listdir(folder):
        fp = os.path.join(folder, fn)
        if os.path.isfile(fp) and not fn.endswith((".py", ".yml", ".docx", ".md")):
            print(fn)
            all_chars = all_chars.union(set(get_all_non_allowed_chars_in_file(fp)))
            print(len(all_chars))
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

get_all_non_allowed_chars_in_folder(".")
    
    
            

