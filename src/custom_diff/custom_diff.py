import sys
import os

FILES_DIR = '.'

# Append directories here to be used by this script in it's search using absolute path

IN_DIRS = []
OUT_FILE = 'output.txt'


if len(sys.argv) < 2:
    print("usage:\n\tcustom_diff.py <input_dir_1> [<input_dir_2>, ...] [-o <out_file>]")

next_is_output = False
for arg in sys.argv[1:]:
    if arg == '-o':
        next_is_output = True
    elif next_is_output:
        OUT_FILE = arg
        next_is_output = False
    else:
        IN_DIRS.append(os.path.abspath(arg))
