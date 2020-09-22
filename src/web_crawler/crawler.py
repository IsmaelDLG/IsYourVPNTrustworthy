#! /usr/bin/python3
"""Module used to crawl the top 500 webpages, according to The Moz Top 500 Websites.

This module contains the necessary code to implement a web crawler that gets and stores each website on the list. It will be used in two environments: one with a VPN installed and one without. This experiment is performed in order to discern wether the VPN is performing JS Injection or not.
"""

import logging
from pathlib import Path
from os import mkdir
import sys
import requests 

LOG_FORMAT = "%(asctime)s|%(name)s|%(module)s|%(levelname)s|%(message)s"
BASE_DIR = str(Path(__file__).parent.absolute().resolve()) + '/'
OUT_DIR = BASE_DIR + 'out/'

_CLASS = "a"
_VERSION = "0"
_SUB = "0"
_PATCH = "0"

if _CLASS == "b":
    _FULL_VERSION = "v%s.%s.%s%s" % (_VERSION, _SUB, _PATCH, _CLASS)
else:
    _FULL_VERSION = "develop"

def _center_string(string, line_size, sep=" "):
    lstr = len(string)
    left_spaces = (line_size - lstr) // 2 if lstr < line_size else 0
    right_spaces = line_size - (left_spaces + lstr) if lstr < line_size else 0
    return sep * left_spaces + string + sep * right_spaces


def _logging_init():
    if not Path(BASE_DIR / Path("log")).exists():
        mkdir(BASE_DIR / Path("log"))
    logging.basicConfig(
        filename=BASE_DIR / Path("log/execution.log"), level=logging.DEBUG, format=LOG_FORMAT
    )
    # sys.stderr = logging.error
    logging.info("#" * 50)
    logging.info(_center_string("Web Crawler %s Started!" % _FULL_VERSION, 50))
    logging.info(_center_string("Using custom crawler built in Python 3.6", 50))
    logging.info("#" * 50)

def get_website_list(filepath: str) -> list:
    """This method parses the document obtained '<from https://moz.com/top500>' into a list object that contains the urls. The .csv file must use the ',' character as separator.

    :param filepath: Path to the .csv file that contains the list.

    :return: A list of URLs, as strings.
    """
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            raw_list = f.readlines()

        raw_list.pop(0)
        clean_list = []
        for row in raw_list:
            field = row.split(',')[1].replace('\"', '')

            if field.startswith("http"):
                clean_list.append(field)
            elif field.startswith("www"):
                clean_list.append("https://" + field)
            else:
                clean_list.append("https://www." + field)
        
        logging.debug('Website list to crawl:')
        logging.debug(clean_list)

    return clean_list

def get_page(url:str) -> str:
    """This method performs a GET request on the given website and returns the response as a Python string.

    Session is not used anymore for it produced unpredictable results.

    :param url: URL of the website to render and save into a file.
    """
    response = requests.get(url)

    return response.text
    
if __name__ == '__main__':
    _logging_init()	
    web_list = get_website_list(BASE_DIR + 'top500Domains.csv')
    
    if not Path(OUT_DIR).exists():
        mkdir(OUT_DIR)

    for page in web_list:
        try:
            a_page = get_page(page)
            with open(OUT_DIR + page.replace("https://", '').replace('.','-') + ".html", 'w') as f:
                f.write(a_page)
        except (Exception) as e:
            logging.error("Unexpected exception: %s" % e)
            


        
    




