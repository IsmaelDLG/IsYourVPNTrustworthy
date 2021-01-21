"""Selenium Crawler Module.

This module is used to look for javascript injection from the extension vpns availible.
"""

import os, sys, zipfile, time, json, threading
from getopt import getopt, GetoptError

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from pathlib import Path

from sort_files import sort
from fancy_hash import calc_proximity_one, calc_proximity_two

DOWNLOAD_DIR = "C:\\Users\\ismae\\Downloads\\"
WEBSITE_LIST = Path('topDomains.csv')
WEBDRIVER = "./chromedriver"
RUNS = 1
CRAWL = True
SHOW_RESULTS = True




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

class Crawler:
    def __init__(self, name, url_list, runs=1, extension=None):
        paths_to_ext = []
        paths_to_ext.append(Path('page_dwnld.crx').absolute())

        if extension:
            paths_to_ext.append(Path(extension).absolute())
        else:
            extension = "no_vpn"
        
        # Create extensions folder
        download_dir = Path(DOWNLOAD_DIR + extension.split(os.path.sep)[-1].split(".")[0])
        if not os.path.exists(str(download_dir)):
            os.mkdir(download_dir)

        exe_path = Path(WEBDRIVER).absolute()
        os.environ["webdriver.chrome.driver"] = str(exe_path)
        
        chrome_options = Options()
        if paths_to_ext:
            for ext in paths_to_ext:
                chrome_options.add_extension(ext)
        # Test
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("prefs", {"download.default_directory" : str(download_dir)})

        self._driver = webdriver.Chrome(executable_path=exe_path, options=chrome_options)
        # Workaround to activate extensions
        wait = True
        while wait:
            wait = input("Start? [y/n]: ") != "y"
        self.visit_all(url_list, runs)

    def clear_data(self):
        self._driver.delete_all_cookies()
        # Obtained from 
        # https://stackoverflow.com/questions/50456783/python-selenium-clear-the-cache-and-cookies-in-my-chrome-webdriver
        self._driver.execute_script("window.open('');")
        time.sleep(0.25)
        self._driver.switch_to.window(self._driver.window_handles[-1])
        time.sleep(0.25)
        self._driver.get('chrome://settings/clearBrowserData') # for old chromedriver versions use cleardriverData
        time.sleep(1)
        actions = ActionChains(self._driver) 
        actions.send_keys(Keys.TAB * 3 + Keys.DOWN * 3) # send right combination
        actions.perform()
        time.sleep(0.5)
        actions = ActionChains(self._driver) 
        actions.send_keys(Keys.TAB * 4 + Keys.ENTER) # confirm
        actions.perform()
        time.sleep(3) # wait some time to finish
        self._driver.close() # close this tab
        self._driver.switch_to.window(self._driver.window_handles[0]) # switch back

    def navigate_to(self, url):
        self._driver.get(url)
        time.sleep(3)
    
    def visit_one(self, url, times):
        for x in range(0, times):
            self.navigate_to(url)
            self.clear_data()
    
    def visit_all(self, url_list, times=1):
        for ws in url_list:
            self.visit_one(ws, times)


if __name__ == '__main__':
    short_opts = "hl:r:t:"
    long_opts = ["help", "list=", "runs=", "threads=", "crawl=", "no-crawl", "no-results"]

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
            new_thread = threading.Thread(
                target=Crawler, args=(timestamp_run, mylist, RUNS, extension), daemon=True)
            new_thread.start()
            thread_list.append(new_thread)

        # Wait for all threads to finish
        for t in thread_list:
            t.join()

    if SHOW_RESULTS:    
        full_result = {}
        simplified_result = {}
        for root in os.listdir(DOWNLOAD_DIR):

            full_result[root] = {}
            simplified_result[root] = {}
            extension_dir = DOWNLOAD_DIR + root + os.path.sep
            # Sort files in directories
            if not os.path.isdir(extension_dir):
                    continue
            files = []
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
                        count = len(os.listdir(file_dir)) +1
                    files.append(name)
                os.rename(extension_dir + f, file_dir + name + '-%i' % count + ".html")
                count = count + 1

            # Analyze the files
            for group in os.listdir(extension_dir):
                group_dir = extension_dir + group
                if not os.path.isdir(group_dir):
                    continue
                else:
                    part_avg, part_data = calc_proximity_one(group_dir)
                    full_result[root][group] = part_data
                    simplified_result[root][group] = part_avg

        with open(DOWNLOAD_DIR + os.path.sep + 'analysis01_full.json', 'w') as f:
            json.dump(full_result, f, indent=2)
        with open(DOWNLOAD_DIR + os.path.sep + 'analysis01_short.json', 'w') as f:
            json.dump(simplified_result, f, indent=2)

    



