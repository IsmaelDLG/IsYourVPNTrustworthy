import os, sys, zipfile, time, json

import chardet    
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from pathlib import Path

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

def ini_driver():
    """Starts with the configuration, returns a web driver."""

    exe_path = Path("./chromedriver")
    os.environ["webdriver.chrome.driver"] = str(exe_path)

    ext_dir = Path('extension')
    ext_file = Path('extension.zip')

    # Create zipped extension
    ## Read in your extension files
    file_names = os.listdir(ext_dir)
    file_dict = {}
    for fn in file_names:
        with open(os.path.join(ext_dir, fn), 'r') as infile:
            file_dict[fn] = infile.read()

    ## Save files to zipped archive
    with zipfile.ZipFile(ext_file, 'w') as zf:
        for fn, content in file_dict.items():
            zf.writestr(fn, content)

    chrome_options = Options()
    chrome_options.add_extension(ext_file)
    chrome_options.add_argument("--enable-benchmarking")

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
        time.sleep(5)
    driver.quit()

def get_scripts_and_iframes(dir_list):
    # Get Scripts and IFrames
    result = {}
    for dir in dir_list:
        for filename in os.listdir(dir):
            if not os.path.isdir(os.path.abspath(dir) + os.path.sep + filename):
                if result.get(filename, None) is None:
                    result[filename] = {}

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
                    result[filename][dir] = {}
                    result[filename][dir]['scripts'] = scripts
                    result[filename][dir]['iframes'] = iframes

    return result

# Check if everyone has the same scripts
def validate_results(data):
    for name in data:
        equal = True
        last = None
        for dir in data[name]:
            if last is not None:
                equal = (last == data[name][dir])
            else:
                last = data[name][dir]

        data[name]["equal"] = equal

def write_results(result):
    """Writes results to file in CWD in json format."""
    with open ("%i.json" % time.time(), 'w') as f:
        json.dump(result, f, indent=4)

if __name__ == '__main__':
    # driver = ini_driver()
    # run_bot(driver)
    write_results(get_scripts_and_iframes(['C:\\Users\\ismae\\Downloads']))

