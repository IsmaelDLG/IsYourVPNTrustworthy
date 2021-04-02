from crawler import CrawlerManager
from datasketch import MinHash
from fancy_hash import create_tree
from result_analysis import (
    repetitions_analysis,
    vpn_common_files,
    discard_resources,
    find_similarities,
    find_uniques,
    vpn_specific_files,
)
import sys, os, time, threading
from json import dump as jdump, JSONEncoder

from getopt import getopt, GetoptError
from pathlib import Path

WEBSITE_LIST = Path("topSospechosos.csv")
RUNS = 1
CRAWL = True
SHOW_RESULTS = True
DOWNLOAD_DIR = "/home/ismael/Descargas/"


def _usage():
    print(
        "\tUsage: {file} [-h|l <path_to_list>|r <n_runs>] extension_1[, ...]".format(
            file=__file__
        )
    )
    print("\tExample:")
    print(
        "\n\tpython {file} -r 5 -l ./mylist.csv ../resources/extensions/chrome/1click.crx".format(
            file=__file__
        )
    )
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


if __name__ == "__main__":
    short_opts = "hl:r:"
    long_opts = ["help", "list=", "runs=", "crawl=", "no-crawl", "no-results"]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        _usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            _usage()
        elif opt in ("-l", "--list"):
            try:
                WEBSITE_LIST = Path(arg).absolute()
            except:
                _usage()
        elif opt in ("-r", "--runs"):
            try:
                RUNS = int(arg)
            except:
                _usage()
        elif opt in ("-t", "--threads"):
            try:
                THREADS_EXT = int(arg)
            except:
                _usage()
        elif opt == "--no-crawl":
            CRAWL = False
        elif opt == "--no-results":
            SHOW_RESULTS = False

    if CRAWL:
        extensions = []
        for extension in args:
            extensions.append(str(Path(extension).absolute()))

        extensions.insert(0, None)  # No extension!

        mylist = get_website_list(WEBSITE_LIST)

        thread_list = []
        timestamp_run = time.time()
        for extension in extensions:
            try:
                new_thread = threading.Thread(
                    target=CrawlerManager,
                    args=(timestamp_run, mylist, RUNS, extension),
                    daemon=True,
                )
                new_thread.start()
            except Exception as e:
                print(
                    'Could not run thread for extension "%s". Error: %s'
                    % (extension, e)
                )
            thread_list.append(new_thread)

        # Wait for all threads to finish
        for t in thread_list:
            t.join()

    if SHOW_RESULTS:
        # Loads all files as fancy_hash
        class MyEncoder(JSONEncoder):
            def default(self, obj):
                if isinstance(obj, MinHash):
                    return {"desc": "MinHash Object", "hash": str(obj.digest())}
                return JSONEncoder.default(self, obj)

        print("Loading files...")
        tree = create_tree(DOWNLOAD_DIR)

        metadata, data = repetitions_analysis(tree)

        with open("results/metadata_analysis.json", "w") as f:
            jdump(metadata, f, indent=4, cls=MyEncoder)

        printable2 = discard_resources(data)

        """
        with open("dynamic_resources_only.json", 'w') as f:
            jdump(printable2, f, indent=4, cls=MyEncoder)
        """

        print("Finding vpn-related files (Not extension-related).")
        present_in_all_vpns, not_present_in_all_vpns = vpn_common_files(metadata)
        with open("results/vpn_related_files.json", "w") as f:
            jdump(present_in_all_vpns, f, indent=4, cls=MyEncode)

        print("Finding files introduced by a specic VPN.")
        vpn_specific_files = vpn_specific_files(not_present_in_all_vpns)
        with open("results/vpn_specific_files.json", "w") as f:
            jdump(vpn_specific_files, f, indent=4, cls=MyEncode)

        print("Finding similarieties...")
        printable3 = find_similarities(printable2)
        del printable2

        """
        with open("dinamyc_resources_similarities.json", 'w') as f:
            jdump(printable3, f, indent=4, cls=MyEncoder)
        """
        printable4 = find_uniques(printable3, similarity_treshold=0.7)
        del printable3

        printable4 = {"total_files": len(printable4), "files": printable4}

        with open("results/resume.json", "w") as f:
            jdump(printable4, f, indent=4, cls=MyEncoder)

# python main.py ../resources/extensions/chrome/1click.crx ../resources/extensions/chrome/adguard.crx ../resources/extensions/chrome/astard.crx ../resources/extensions/chrome/betternet.crx
# python main.py ../resources/extensions/chrome/browsec.crx ../resources/extensions/chrome/earth.crx

# python main.py ../resources/extensions/chrome/earth.crx ../resources/extensions/chrome/free.pro.crx ../resources/extensions/chrome/hola.crx  ../resources/extensions/chrome/hotspot.crx
# python main.py ../resources/extensions/chrome/hoxx.crx ../resources/extensions/chrome/ip_unblock.crx ../resources/extensions/chrome/ivacy.crx
# python main.py ../resources/extensions/chrome/phoenix.crx ../resources/extensions/chrome/pp.crx ../resources/extensions/chrome/prime.crx ../resources/extensions/chrome/pron.crx
# python main.py ../resources/extensions/chrome/rusvpn.crx ../resources/extensions/chrome/surf.crx ../resources/extensions/chrome/touch.crx ../resources/extensions/chrome/tuxler.crx
# python main.py ../resources/extensions/chrome/unlimited.crx ../resources/extensions/chrome/urban.crx ../resources/extensions/chrome/veepn.crx ../resources/extensions/chrome/vpnproxymaster.crx ../resources/extensions/chrome/zenmate.crx
