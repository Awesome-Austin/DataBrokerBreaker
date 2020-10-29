import os

from definitions import OUTPUT_DIR
from removers.spokeo import SpokeoRemovr

# for folder_name, subfolders, filenames in os.walk(OUTPUT_DIR):
#     print(folder_name)
#     for subfolder in subfolders:
#         print(f'\t└ {subfolder}')
#         for file in filenames


for folder_name, subfolders, file_names in os.walk(os.path.join(OUTPUT_DIR, 'Austin_Gifford')):
    for file_name in file_names:
        print(folder_name)
        with SpokeoRemovr(os.path.join(folder_name, file_name)) as s:
            s.opt_out()


