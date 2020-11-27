import os
import re
from openiti.helper.uri import URI
from textwrap import wrap

r = "Y"

coll_dict = dict()
i = 0
tot = 0
for fn in os.listdir("."):
    date = fn[:4]
    if "Diwan" in fn and "ShamAY" in fn and int(date)<460:
##    if "0001QaysIbnKhatim" in fn:
        with open(fn, mode="r", encoding="utf-8") as file:
            text = file.read()
##            print(fn, "ENDNOTES" in text)
##            endnotes= re.findall("ENDNOTES.+", text, flags=re.DOTALL)[0]
##            empty_page = "(?<=PageV[^P]{2}P\d{3})[\r\n]+PageV[^P]{2}P\d{3}"
##            print(re.findall(empty_page, endnotes))
        print()
        print("**"*60)
        print(fn)
        text = re.sub("######OpenITI#META# ", "######OpenITI#\n\n#META# ", text)
        text = re.sub("#META#Header#End#? ?(?![\r\n# ])",
                      "#META#Header#End#\n\n# ", text)
        header = re.findall("######OpenITI#.+#META#Header#End#", text,
                            flags=re.DOTALL)[0]
        header = re.sub(r"[\r\n]+#([^#M])", r" (\1", header)
        

        text = re.sub(" +%~% +", " %~% ", text)
        text = re.sub(r"([\r\n]+)#? ?(البحر : \w+) \(",
                      r"\1# \2\n# ", text)
        ###
        text = re.sub(r"\r?\n?~~", " ", text)
        text = re.sub(r"\(([^*]*) \*\* ([^\)]*?) ?\) ?(\d*)",
                      r"\r\n# \1 %~% \2 \3", text)
        text = re.sub("(البحر : .+)", r"\n\n# \1", text)
        text = re.sub(" +", " ", text)
        text = re.sub("[\r\n]+# +(?=[\r\n])", "", text)
        text = re.sub("[\r\n]+# (?!البحر)", "\n# ", text)

        text = re.sub("# ###", "###", text)

        text = re.sub("######OpenITI#.+#META#Header#End#", header,
                      text, flags=re.DOTALL)
        print(text[:12000])
##        text = re.sub("[\r\n]+~~", " ", text)
##        text = re.sub(r"(?: \d+)? ?\( ?([^\*]+)\*\*([^\)]+)\) ?\d*", r"\n# \1 %~% \2", text)
##        text = re.sub(" (PageV[^P]+P\d+) البحر :", r"\n\1\n# البحر :", text)
##        text = re.sub("(PageV[^P]+P\d+[\r\n]+)+PageV[^P]+P\d+", "", text)
##        text = re.sub(r"[\r\n]+#? ?### \|EDITOR\|[\r\n]+# ENDNOTES[\r\n]+\Z", "", text)
##        text = re.sub("# ?[\r\n]+", "", text)
##        print(text)
##        
        #r = input(fn + " Change? Y/N: ")
        if r.lower() == "y":
            with open(fn, mode="w", encoding="utf-8") as file:
                file.write(text)

##    if "Sham19Y" in fn and "0354IbnHibbanBusti.Sahih" not in fn:
        if int(fn[:4]) > 0:
            with open(fn, mode="r", encoding="utf-8") as file:
                text = file.read()
            print()
            print("**"*60)
            print(fn)
            try:
                
            #text = re.sub("(PageV[^P]+P\d+) #", r"\1\n#", text)
                if "Endnotes" in text or "ENDNOTES" in text:
                    text = re.sub(r"(PageV[^P]+P\d+): ?([^P]+)(?=Page|\Z)",
                                  r"\2\1", text)
                    endnotes = re.findall("(?:Endnotes|ENDNOTES).+", text,
                                          flags=re.DOTALL)[0]
                    endnotes = re.split("([\r\n]+)", endnotes)
                    new = []
                    for line in endnotes:
                        if line.startswith("("):
                            new.append("# " + "\n~~".join(wrap(line)))
                        else:
                            new.append(line)
                            
                    text = re.sub("(?:Endnotes|ENDNOTES).+", "".join(new),
                                  text, flags=re.DOTALL)
                    empty_page = "(?<=PageV[^P]{2}P\d{3})[\r\n]+PageV[^P]{2}P\d{3}"
                    text = re.sub(empty_page, "", text)
                    empty_page = "(?<=PageV[^P]{2}P\d{3})[\r\n]+PageV[^P]{2}P\d{4}"
                    text = re.sub(empty_page, "", text)
                    empty_page = "(?<=PageV[^P]{2}P\d{4})[\r\n]+PageV[^P]{2}P\d{4}"
                    text = re.sub(empty_page, "", text)
                    empty_page = "(?<=ENDNOTES)[\r\n]+PageV[^P]{2}P\d{3}"
                    text = re.sub(empty_page, "", text)

                    text = re.sub("[\r\n]+### \|EDITOR\|[\r\n]+#? ?ENDNOTES[\r\n ]*\Z",
                                  "", text)
                    
                    print(text[-5000:])
                    #r = input(fn + " Change? Y/N: ")
                    if r.lower() == "y":
                        with open(fn, mode="w", encoding="utf-8") as file:
                            file.write(text)
                else:
                    print("No Endnotes")
                    text = re.sub(" \d+ ?(?=Page|[\r\n]+#)", "", text)
                    #input("Continue?")
                    print(text[-5000:])
                    r = input(fn + " Change? Y/N: ")
                    if r.lower() == "y":
                        with open(fn, mode="w", encoding="utf-8") as file:
                            file.write(text)
            except Exception as e:
                print("FAILURE in", fn)
                print(e)
                #input("CONTINUE?")
        
##
####    if "-ara" in fn and not fn.endswith("yml"):
####        tot += 1
####        coll = re.findall("(\w+?[^\d\-])\d+-ara", fn)[0]
####        if coll not in coll_dict:
####            coll_dict[coll] = 0
####        coll_dict[coll] += 1
####        u = URI(fn)
####        u.base_pth = r"D:\London\OpenITI\25Y_repos"
####        book_fp = u.build_pth("book_yml")
####        #print(book_fp)
####        if not os.path.exists(book_fp):
####            i += 1
####            print(i, fn)
####print("total:", tot, "books")
####for coll in coll_dict:
####    print("{}: {} texts: ".format(coll, coll_dict[coll]))
        
