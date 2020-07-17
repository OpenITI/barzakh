"""Run this script to push the files in the barzakh repo to the
correct folder in the corpus.

NB: make sure to make sure all repos are up to date by pulling all of them
before running this script."""

import os
from openiti.new_books.add.add_books import initialize_new_text

folder = "."
target_base_pth = r"D:\London\OpenITI\25Y_repos"
ignore = (".yml", ".md", ".py", ".git", ".gitignore")


for fn in os.listdir(folder):
    if fn.endswith(ignore):
        print(fn, "ignored because of its extension")
    elif "oorlib" in fn:
        print(fn, "ignored because it is a Noorlib file")
    else:
        fp = os.path.join(folder, fn)
        print(fp)
        if os.path.isfile(fp):
            initialize_new_text(fp, target_base_pth, execute=False)
 

#initialize_new_texts_in_folder(".", r"D:\London\OpenITI\25Yrepos")
