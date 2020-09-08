import os
import re


def get_avg_line_len(text):
    """Compute the average length of a line of text
    (not including page numbers on a new line and titles)"""
    lines = []
    for line in text.splitlines():
        if not line.startswith(("#", "P")) and line != "":
            print(len(line))
            lines.append(len(line))
    return (sum(lines) / len(lines))


def add_paragraph_marks_to_file(fp):
    """Add paragraph marks (hashtags and tildas) to one file."""
    with open(fp, mode="r", encoding="utf-8") as file:
        text = file.read().strip()
    #avg_len = get_avg_line_len(text)

    # add # after line that ends with full stop, question and exclamation marks:
    ptrn = r"([.؟!] *[\r\n]+(?:PageV\w{2}P\d+[\r\n]+)?)([^\r\n#P\Z])"
    text = re.sub(ptrn, r"\1# \2", text)

    # add # after section titles (but not before page numbers and sub-titles)
    ptrn = r"(### .+[\r\n]+(?:PageV\w{2}P\d+[\r\n]+)?)([^\r\n#P\Z])"
    text = re.sub(ptrn, r"\1# \2", text)

    #  add the tildas for continued lines:
    new_text = ""
    for line in re.split(r"([\r\n]+)", text):
        if not line.startswith(("P", "#", "~~")) and not re.match(r"([\r\n]+)", line):
            line = "~~"+line
        new_text += line

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
    fp = "0711IbnIbrahimCimadDinWasiti.Rihla.LMN20200830-ara1.completed"
    add_paragraph_marks_to_file(fp)

    folder = "."
    add_paragraph_marks_to_folder(folder)
