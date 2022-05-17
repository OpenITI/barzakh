from openiti.helper.funcs import get_all_yml_files_in_folder, exclude_folders
from openiti.helper.yml import readYML
import os

exclude_folders += ["safe", "meta", ".github"]

for fp in get_all_yml_files_in_folder(".", ["version"], excluded_folders=exclude_folders):
    
    try:
        y = readYML(fp)
        if "Kraken" in fp and "12-24-2021" not in y["90#VERS#COMMENT##:"]:
            print(".".join(os.path.split(fp)[-1].split(".")[:2]))
    except:
        pass
