"""Selenium Crawler Module.

This module is used to look for javascript injection from the extension vpns availible.
"""

import os, sys, zipfile, time, json

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from pathlib import Path

##### UTILS #####

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

##### CRAWLER CODE #####

def prepare_extension(ext):
    ext_files = []
    ext_files.append(Path('page_dwnld.crx').absolute())
    if ext:
        ext_files.append(Path(ext).absolute())

    return ext_files

def ini_driver(browser, ext):
    """Starts with the configuration, returns a web driver."""
    
    # We only need an extension at a time
    exetensions_path = prepare_extension(ext)

    if browser == "chrome":
        exe_path = Path("./chromedriver").absolute()
        os.environ["webdriver.chrome.driver"] = str(exe_path)

        chrome_options = Options()
        if exetensions_path:
            for ext in exetensions_path:
                chrome_options.add_extension(ext)
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(executable_path=exe_path, options=chrome_options)
    
    return driver

def run_bot(driver):
    """Main method.
    
    Downloads each of the pages in the 500 list and finds scripts and iframes.
    """
    mylist = get_website_list(Path('top500Domains.csv'))
    for web in mylist:
        print(web)
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

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        
        # Without any extension
        driver = ini_driver("chrome", None)
        run_bot(driver)
        rename_files("C:\\Users\\ismae\\Downloads", "no_vpn")
        
        for extension in sys.argv[1:]:
            driver = ini_driver("chrome", extension)
            # Give me time to activate the extension manually!
            wait = True
            while wait:
                wait = input("Start? [y/n]: ") != "y"
            run_bot(driver)
            rename_files("C:\\Users\\ismae\\Downloads", extension.split(os.path.sep)[-1].split(".")[0])
        
        result = get_scripts_and_iframes(["C:\\Users\\ismae\\Downloads"])
        result = validate_results(result)
        write_results(result)

        


