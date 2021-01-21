"""Selenium Crawler Module.

This module is used to look for javascript injection from the extension vpns availible.
"""

import os, sys, zipfile, time, json, threading
from getopt import getopt, GetoptError

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from pathlib import Path

from sort_files import sort
from fancy_hash import calc_proximity_one, calc_proximity_two

DOWNLOAD_DIR = "C:\\Users\\ismae\\Downloads"

WEBSITE_LIST = Path('top500Domains.csv')

RUNS = 1

THREADS_EXT = 1

##### UTILS #####

def _usage():
    print("\tusage: {file} [-h|l <path_to_list>|r <n_runs>|t <n_threads>] extension_1[, ...]".format(file=__file__))
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

            if field.startswith("http"):
                clean_list.append(field)
            elif field.startswith("www"):
                clean_list.append("https://" + field)
            else:
                clean_list.append("https://www." + field)

    return clean_list

def rename_files(dir, pattern):
    pre_pattern = "###"
    for f in os.listdir(dir):
        if not pre_pattern in f:
            if f.split(".")[-1] == "html":
                done = False
                number = 0
                while not done:
                    try:
                        os.rename(dir + os.path.sep + f, dir + os.path.sep + pattern + pre_pattern + str(number) + f)
                        done = True
                    except FileExistsError:
                        number = number +1

##### CRAWLER CODE #####

def prepare_extension(ext):
    ext_files = []
    ext_files.append(Path('page_dwnld.crx').absolute())
    if ext:
        ext_files.append(Path(ext).absolute())

    return ext_files

def ini_driver(crawl_id, browser, ext):
    """Starts with the configuration, returns a web driver."""
    
    # We only need an extension at a time
    exetensions_path = prepare_extension(ext)
    if not ext:
        ext = "no_vpn"

    if browser == "chrome":
        download_dir = Path("C:\\Users\\ismae\\Downloads\\%s" % ext.split(os.path.sep)[-1].split(".")[0])
        if not os.path.exists(str(download_dir)):
            os.mkdir(download_dir)
        
        # run?
        download_dir = str(download_dir) + os.path.sep + str(Path(str(crawl_id)))
        if not os.path.exists(str(download_dir)):
            os.mkdir(download_dir)

        exe_path = Path("./chromedriver").absolute()
        os.environ["webdriver.chrome.driver"] = str(exe_path)

        chrome_options = Options()
        if exetensions_path:
            for ext in exetensions_path:
                chrome_options.add_extension(ext)
        # Test
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {"download.default_directory" : str(download_dir)})
        driver = webdriver.Chrome(executable_path=exe_path, options=chrome_options)

    return driver

def run_bot(driver, mylist):
    """Main method.
    
    Downloads each of the pages in the 500 list and finds scripts and iframes.
    """

    wait = True
    while wait:
        wait = input("Start? [y/n]: ") != "y"

    for web in mylist:
        try:
            driver.get(web)
        except:
            continue
        time.sleep(4)
    driver.quit()

def get_scripts_and_iframes(dir_list):
    # Get Scripts and IFrames
    result = {}
    dir = "C:\\Users\\ismae\\Downloads"
    for filename in os.listdir(dir):
        if not os.path.isdir(os.path.abspath(dir) + os.path.sep + filename):
            try:
                vpn, page = filename.split("###")
            except:
                continue
            if result.get(page, None) is None:
                result[page] = {}

            with open(os.path.abspath(dir) + os.path.sep + filename, 'r') as fd:
                try:
                    rawdata = fd.read()
                except:
                    continue
                
                soup = BeautifulSoup(rawdata, 'html.parser')
                scripts = []
                [scripts.append(str(x)) for x in soup.find_all('script')]
                iframes = []
                [iframes.append(str(x)) for x in soup.find_all('iframe')]
                result[page][vpn] = {}
                result[page][vpn]['scripts'] = scripts
                result[page][vpn]['iframes'] = iframes

    return result

##### OUTPUT #####
                    
def validate_results(data):
    """Checks wether a VPN has injected code into a certain webpage.

    NOT IMPLEMENTED
    """
    for name in data:
        equal = True
        last = None
        for vpn in data[name]:
            if last is not None:
                equal = (last == data[name][vpn])
            else:
                last = data[name][vpn]

        data[name]["equal"] = equal
    return data

def write_results(result):
    """Writes results to file in CWD in json format."""
    with open ("%i.json" % time.time(), 'w') as f:
        json.dump(result, f, indent=4)

##### MAIN #####

def crawl_list(crawl_id, mylist, extension):
    driver = ini_driver(crawl_id, "chrome", extension)
    run_bot(driver, mylist)

def check_dirs(ini_dir):
    """Return dirs with html files.
    """
    check_dirs = []
    for vpn_dir in os.listdir(ini_dir):
        if os.path.isdir(ini_dir + os.path.sep + vpn_dir):
            for run_dir in os.listdir(ini_dir + os.path.sep + vpn_dir):
                if os.path.isdir(ini_dir + os.path.sep + vpn_dir + os.path.sep + run_dir):
                    check_dirs.append(ini_dir + os.path.sep + vpn_dir + os.path.sep + run_dir)
    return check_dirs


if __name__ == '__main__':
    short_opts = "hl:r:t:"
    long_opts = ["help", "list=", "runs=", "threads="]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        _usage()

    if len(args) < 1:
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
    
    extensions = []
    for extension in args:
        extensions.append(str(Path(extension).absolute()))
    
    extensions.insert(0, None) # No extension!
    
    mylist = get_website_list(WEBSITE_LIST)

    if RUNS > 1:
    else:   
        timestamp_run = time.time()
        thread_list = []
        for ext in extensions:
            step = len(mylist)/THREADS_EXT
            for thread in range(THREADS_EXT):
                # Spawn Threads
                current = int(step*thread)
                end = int(current + step - 1)
                new_thread = threading.Thread(
                    target=crawl_list, args=(timestamp_run, mylist[current:end], ext), daemon=True)
                new_thread.start()
                thread_list.append(new_thread)
        
        # Wait for all threads to finish
        for t in thread_list:
            t.join()

    sort(DOWNLOAD_DIR)
    full_result = {}
    simplified_result = {}
    for root in os.listdir(DOWNLOAD_DIR):
        full_result[root] = {}
        simplified_result[root] = {}
        # Case dir
        case = DOWNLOAD_DIR + os.path.sep + root
        if not os.path.isdir(case):
                continue
        for group in os.listdir(case):
            if not os.path.isdir(case + os.path.sep + group):
                continue
            if group.startswith("file-"):
                part_avg, part_data = calc_proximity_one(case + os.path.sep + group)
                full_result[root][group] = part_data
                simplified_result[root][group] = part_avg
    
    with open(DOWNLOAD_DIR + os.path.sep + 'analysis01_full.json', 'w') as f:
        json.dump(full_result, f, indent=2)
    with open(DOWNLOAD_DIR + os.path.sep + 'analysis01_short.json', 'w') as f:
        json.dump(simplified_result, f, indent=2)
    
    res2 = calc_proximity_two(DOWNLOAD_DIR)
    with open(DOWNLOAD_DIR + os.path.sep + 'analysis02.json', 'w') as f:
        json.dump(res2, f, indent=2)

    

        
# python .\selenium_crawler.py --runs 8 --threads 2 ..\resources\extensions\chrome\1click.crx ..\resources\extensions\chrome\astard.crx ..\resources\extensions\chrome\betternet.crx ..\resources\extensions\chrome\browsec.crx ..\resources\extensions\chrome\daily.crx ..\resources\extensions\chrome\earth.crx ..\resources\extensions\chrome\free.pro.crx ..\resources\extensions\chrome\hotspot.crx ..\resources\extensions\chrome\ivacy.crx ..\resources\extensions\chrome\phoenix.crx ..\resources\extensions\chrome\pp.crx ..\resources\extensions\chrome\prime.crx ..\resources\extensions\chrome\pron.crx
# python .\selenium_crawler.py --runs 10 ..\resources\extensions\chrome\1click.crx ..\resources\extensions\chrome\astard.crx ..\resources\extensions\chrome\betternet.crx ..\resources\extensions\chrome\browsec.crx ..\resources\extensions\chrome\earth.crx ..\resources\extensions\chrome\free.pro.crx ..\resources\extensions\chrome\hotspot.crx ..\resources\extensions\chrome\phoenix.crx ..\resources\extensions\chrome\pp.crx ..\resources\extensions\chrome\prime.crx ..\resources\extensions\chrome\pron.crx
# https://stackoverflow.com/questions/49614217/selenium-clear-chrome-cache