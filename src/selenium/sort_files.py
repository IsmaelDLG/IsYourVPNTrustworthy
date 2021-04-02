import os, sys
from shutil import copyfile
from getopt import getopt, GetoptError


INPUT_DIR = "C:\\Users\\ismae\\Downloads"

"""This is just a helper script to execute the crawl and the processs scripts!

I asume the directory hierarchy follows this structure.

- INPUT_DIR
    - TEST_CASE_1
        - RUN_1
            - FILE_1
            - FILE_2
            - FILE_3
        - RUN_2
            - FILE_1
    - TEST_CASE_2
        - RUN_1
            - FILE_1
            - FILE_2

This script copies the same files from different runs in a single dir so that the process_crawl_results script works.
"""


def _usage():
    print("\tusage: {file} [-h|d <directory>]".format(file=__file__))
    sys.exit(2)


def sort(input_dir=INPUT_DIR):
    files = {}
    # Root dirs
    for root in os.listdir(INPUT_DIR):
        # Case dir
        case = INPUT_DIR + os.path.sep + root
        files[root] = {}
        count = 0
        if not os.path.isdir(case):
            continue
        for r in os.listdir(case):
            # Run dir
            run = case + os.path.sep + r
            if not os.path.isdir(run):
                continue
            for f in os.listdir(run):
                fname = f.split(".")[0]
                if fname.startswith("file-"):
                    continue
                a_file = run + os.path.sep + f
                dirname = case + os.path.sep + "file-" + fname
                if fname in files[root]:
                    print(
                        "copying file %s to %s"
                        % (a_file, dirname + os.path.sep + "file-" + str(count))
                    )
                    copyfile(
                        a_file, dirname + os.path.sep + "file-" + str(count) + ".txt"
                    )
                else:
                    if not os.path.exists(dirname):
                        os.mkdir(dirname)
                    files[root][fname] = (
                        dirname + os.path.sep + "file-" + str(count) + ".txt"
                    )
            count = count + 1
        print("Finished case %s." % root)


if __name__ == "__main__":
    short_opts = "hd:"
    long_opts = ["help", "directory="]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        print("Couldn't get options!")
        _usage()

    for opt, val in opts:
        if opt in ("-h", "--help"):
            _usage()
        elif opt in ("-d", "--directory"):
            try:
                INPUT_DIR = str(Path(val).absolute())
            except:
                _usage()

    sort()
