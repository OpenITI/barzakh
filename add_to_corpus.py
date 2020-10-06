"""Run this script to push the files in the barzakh repo to the
correct folder in the corpus.

NB: make sure to make sure all repos are up to date by pulling all of them
before running this script."""

import os
from openiti.new_books.add.add_books import initialize_new_text

folder = "."
target_base_pth = r"D:\London\OpenITI\25Y_repos"
ignore = (".yml", ".md", ".py", ".git", ".gitignore", ".txt")

logfp = "log.md"

changed_repos = set()

#with open(logfp, mode="a", encoding="utf-8") as log_file:
for fn in os.listdir(folder):
    if fn.endswith(ignore):
        print(fn, "ignored because of its extension")
    elif "oorlib" in fn:
        print(fn, "ignored because it is a Noorlib file")
    else:
        fp = os.path.join(folder, fn)
        print(fp)
        if os.path.isfile(fp):
            initialize_new_text(fp, target_base_pth, execute=True)
            y = int(fn[:4])
            repo = "{0:04d}AH".format(y-(y%25))
            changed_repos.add(os.path.join(target_base_pth, repo))
            repo = "{0:04d}AH".format(int(fn[:4]))
            #log_file.write("Moved" + fp + "\n")

print("Done!")

if changed_repos:
    print("Changed repos:")
    for repo in sorted(list(changed_repos)):
        print(repo)
    with open("changed_repos.txt", mode="w", encoding="utf-8") as file:
        file.write("\n".join(sorted(list(changed_repos))))

    # this doesn't work yet...
    print("Run the following commands in Git bash to push the changes:")
    cmd = "while read -r line do \
    (cd $line; \
    git add .; \
    git commit -m 'Added files from barzakh'; \
    git push origin master; \
    done;) < changed_repos.txt"
    print(cmd)
 

#initialize_new_texts_in_folder(".", r"D:\London\OpenITI\25Yrepos")
