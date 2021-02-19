from crawler import CrawlerManager
from fancy_hash import  create_tree
from result_analysis import repetitions, discard_resources, find_similarities
import sys, os, time, threading
from json import dump as jdump
from getopt import getopt, GetoptError
from pathlib import Path

WEBSITE_LIST = Path('topSospechosos.csv')
RUNS = 1
CRAWL = True
SHOW_RESULTS = True
DOWNLOAD_DIR = "/home/ismael/Descargas/"

def _usage():
    print("\tUsage: {file} [-h|l <path_to_list>|r <n_runs>] extension_1[, ...]".format(file=__file__))
    print("\tExample:")
    print("\n\tpython {file} -r 5 -l ./mylist.csv ../resources/extensions/chrome/1click.crx".format(file=__file__))
    sys.exit(2)

def get_website_list(filepath: str) -> list:
    """This method parses the document obtained from https://moz.com/top500 into a list 
    object that contains the urls. The .csv file must use the ',' character as 
    separator.

    :param filepath: Path to the .csv file that contains the list.

    :return: A list of URLs, as strings.
    """
    clean_list = []

    if Path(filepath).exists():
        with open(filepath, "r") as f:
            raw_list = f.readlines()

        raw_list.pop(0)
        for row in raw_list:
            field = row.split(",")[1].replace('"', "")

            clean_list.append(field)

    return clean_list

if __name__ == '__main__':
    short_opts = "hl:r:"
    long_opts = ["help", "list=", "runs=", "crawl=", "no-crawl", "no-results"]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        _usage()
    
    for opt, arg in opts:
        if opt in ('-h', '--help') :
            _usage()
        elif opt in ('-l', '--list'):
            try:
                WEBSITE_LIST = Path(arg).absolute()
            except:
                _usage()
        elif opt in ('-r', '--runs'):
            try:
                RUNS = int(arg)
            except:
                _usage()
        elif opt in ('-t', '--threads'):
            try:
                THREADS_EXT = int(arg)
            except:
                _usage()
        elif opt == '--no-crawl':
            CRAWL = False
        elif opt == '--no-results':
            SHOW_RESULTS = False
    
    if CRAWL:
        extensions = []
        for extension in args:
            extensions.append(str(Path(extension).absolute()))
        
        extensions.insert(0, None) # No extension!
        
        mylist = get_website_list(WEBSITE_LIST)

        thread_list = []
        timestamp_run = time.time()
        for extension in extensions:
            try:
                new_thread = threading.Thread(
                    target=CrawlerManager, args=(timestamp_run, mylist, RUNS, extension), daemon=True)
                new_thread.start()
            except Exception as e:
                print("Could not run thread for extension \"%s\". Error: %s" % (extension, e))
            thread_list.append(new_thread)

        # Wait for all threads to finish
        for t in thread_list:
            t.join()

    if SHOW_RESULTS:    
        # Loads all files as fancy_hash
        tree = create_tree(DOWNLOAD_DIR)

        printable1 = repetitions(tree)

        import json
        with open("test1.json", 'w') as f:
            json.dump(printable1, f, indent=4)
        
        printable2 = discard_resources(printable1)

        with open("test2.json", 'w') as f:
            json.dump(printable2, f, indent=4)
        
        # find_similarities(printable2)
