from crawler import CrawlerManager
import sys, os, time, threading
from json import dump as jdump
from getopt import getopt, GetoptError
from pathlib import Path

WEBSITE_LIST = Path('topSospechosos.csv')
RUNS = 1
CRAWL = True
SHOW_RESULTS = False
DOWNLOAD_DIR = "/home/ismael/Downloads/"

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
        full_result = {}
        simplified_result = {}
        for root in os.listdir(DOWNLOAD_DIR):
            print("Sorting files for extension %s..." % root)
            full_result[root] = {}
            simplified_result[root] = {}
            extension_dir = DOWNLOAD_DIR + root + os.path.sep
            # Sort files in directories
            if not os.path.isdir(extension_dir):
                    continue
            files = {}
            count = 0
            for f in os.listdir(extension_dir):
                if os.path.isdir(extension_dir + f):
                    continue
                name = f.split(".")[0].split(" ")[0]
                file_dir = extension_dir + name + os.path.sep
                if name not in files:
                    if not os.path.exists(file_dir):
                        os.mkdir(file_dir)  
                    else:
                        count = len(os.listdir(file_dir)) + 1
                    files[name] = count
                os.rename(extension_dir + f, file_dir + name + '-%i' % files[name] + ".html")
                files[name] = files[name] + 1
            print("Finished.")
            # Analyze the files
            print("Calculating proximity of files using extension %s..." % root)
            for group in os.listdir(extension_dir):
                group_dir = extension_dir + group
                if not os.path.isdir(group_dir):
                    continue
                else:
                    part_avg, part_data = calc_proximity_of_dir(group_dir)
                    full_result[root][group] = part_data
                    simplified_result[root][group] = part_avg
            print("Finished.")

        with open(DOWNLOAD_DIR + os.path.sep + 'analysis01_full.json', 'w') as f:
            jdump(full_result, f, indent=2)
        with open(DOWNLOAD_DIR + os.path.sep + 'analysis01_short.json', 'w') as f:
            jdump(simplified_result, f, indent=2)