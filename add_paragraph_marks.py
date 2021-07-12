import os
import re
import textwrap


def get_avg_line_len(text):
    """Compute the average length of a line of text
    (not including page numbers on a new line and titles)"""
    lines = []
    for line in text.splitlines():
        if not line.startswith(("#", "P")) and line != "":
            print(len(line))
            lines.append(len(line))
    return (sum(lines) / len(lines))

def wrap(text, max_length=72):
    header, text = re.split("#META#Header#End#", text)
    header += "#META#Header#End#"
    wrapped = []
    for line in re.split("([\r\n]+)", text):
        if line.startswith(("###", "\r", "\n")):
            wrapped.append(line)
        else:
            lines = textwrap.wrap(line, max_length, break_long_words=False)
            wrapped.append("\n~~".join(lines))

    return header + "".join(wrapped)
    

def add_paragraph_marks_to_file(fp, keep_line_endings=True):
    """Add paragraph marks (hashtags and tildas) to one file.

    Args:
        fp (str): path to the file
        keep_line_endings (bool): if True, line endings in the original file
            will be kept; if False, long lines will be broken into
            shorter lines.
    """
    with open(fp, mode="r", encoding="utf-8") as file:
        text = file.read().strip()
    #avg_len = get_avg_line_len(text)

    # add # after line that ends with full stop, question and exclamation marks:
    ptrn = r"([.؟!] *[\r\n]+(?:PageV\w{2}P\d+[\r\n]+)?)([^\r\n#P\Z])"
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
        new_text = wrap(text)

    new_text = re.sub("~~#", "#", new_text)
    new_text = re.sub(r"~~([^\n]+%~%)", r"# \1", new_text)
    new_text = re.sub(r"~~\.\./", "../", new_text)


    # save text:
    with open(fp, mode="w", encoding="utf-8") as file:
        file.write(new_text)

def add_paragraph_marks_to_folder(folder, ext=("completed", "mARkdown")):
    """Add paragraph marks to all files in folder if their extension is in `ext`
    """
    for fn in os.listdir(folder):
        if fn.endswith(ext):
            fp = os.path.join(folder, fn)
            add_paragraph_marks_to_file(fp)

if __name__ == "__main__":
    fp = "0216IbnQuraybAsmaci.Khayl.GVDB20210524-ara1.completed"
    add_paragraph_marks_to_file(fp, keep_line_endings=False)
    input("Continue?")
    folder = "."
    add_paragraph_marks_to_folder(folder)
