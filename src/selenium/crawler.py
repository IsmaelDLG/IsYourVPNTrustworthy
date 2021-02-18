"""Selenium Crawler Module.

This module is used to look for javascript injection from the extension vpns availible.
"""

import os
from time import sleep, time
from json import loads as jloads
from datetime import datetime, timezone
import requests
from hashlib import md5
import traceback 
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

WEBDRIVER = "/usr/bin/chromedriver"

def utc_now():
    return datetime.utcnow().replace(tzinfo=timezone.utc)


class Crawler:
    def __init__(self, runs=1, extension=None, current_url=0, current_run=0, download_dir="/home/ismael/Downloads/"
):
        self._runs_per_site = runs
        self._extension = extension

        self._current_url = current_url
        self._current_run = current_run

        paths_to_ext = []
        # Our extensions, which downloads the scripts of the webpage
        paths_to_ext.append(Path('page_dwnld.crx').absolute())

        if extension:
            paths_to_ext.append(Path(extension).absolute())
        else:
            extension = "no_vpn"
        
        # Create download folder
        download_dir = download_dir + extension.split(os.path.sep)[-1].split(".")[0] + os.path.sep
        if not os.path.exists(str(download_dir)):
            os.mkdir(download_dir)

        self._download_dir = download_dir

        self._exe_path = Path(WEBDRIVER).absolute()
        os.environ["webdriver.chrome.driver"] = str(self._exe_path)

        self._chrome_options = Options()
        if paths_to_ext:
            for ext in paths_to_ext:
                self._chrome_options.add_extension(ext)
        # Test
        
        self._chrome_options.add_argument('--no-sandbox')
        self._chrome_options.add_argument('--disable-dev-shm-usage')
        self._chrome_options.add_experimental_option('useAutomationExtension', False)
        self._chrome_options.add_experimental_option("prefs", {"download.default_directory" : str(download_dir)})

        # Clean cache/cookies
        self._chrome_options.add_argument('--media-cache-size=0')
        self._chrome_options.add_argument('--v8-cache-options=off')
        self._chrome_options.add_argument('--disable-gpu-program-cache')
        self._chrome_options.add_argument('--gpu-program-cache-size-kb=0')
        self._chrome_options.add_argument('--disable-gpu-shader-disk-cache')
        self._chrome_options.add_argument('--disk-cache-dir=/tmp')
        self._chrome_options.add_argument('--disable-dev-shm-usage')
        self._chrome_options.add_argument('--v8-cache-strategies-for-cache-storage=off')
        self._chrome_options.add_argument('--mem-pressure-system-reserved-kb=0')
        self._chrome_options.set_capability("applicationCacheEnabled", False)

        # Set Devtools Protocol to start taking network logs
        self._chrome_options.set_capability("loggingPrefs", {'performance': 'ALL'})
        self._chrome_options.add_experimental_option('w3c', False)

        self._driver = webdriver.Chrome(executable_path=self._exe_path, options=self._chrome_options)

    def clear_data(self):
        self._driver.delete_all_cookies()
        # Obtained from 
        # https://stackoverflow.com/questions/50456783/python-selenium-clear-the-cache-and-cookies-in-my-chrome-webdriver
        self._driver.execute_script("window.open('');")
        sleep(0.25)
        self._driver.switch_to.window(self._driver.window_handles[-1])
        sleep(0.25)
        self._driver.get('chrome://settings/clearBrowserData') # for old chromedriver versions use cleardriverData
        sleep(1)
        actions = ActionChains(self._driver) 
        actions.send_keys(Keys.TAB * 3 + Keys.DOWN * 3) # send right combination
        actions.perform()
        sleep(0.5)
        actions = ActionChains(self._driver) 
        actions.send_keys(Keys.TAB * 4 + Keys.ENTER) # confirm
        actions.perform()
        sleep(3) # wait some time to finish
        self._driver.close() # close this tab
        self._driver.switch_to.window(self._driver.window_handles[0]) # switch back
    
    def _download_file(self, url, destination, headers=None, verify=True):
        """ Downloads a file. """

        h = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'}
        if headers is not None:
            h.update(headers)

        resp = requests.get(url, stream=True, headers=h, timeout=(6, 27), verify=verify)
        for chunk in resp.iter_content(chunk_size=4096):
            if chunk:
                destination.write(chunk)

        destination.seek(0)
        return destination, resp.headers

    def download_resources(self, domain, request):
        """Downloads requests' resources.
        
        :returns: None.
        """

        if "mime_type" in request and any(case in request["mime_type"] for case in ("text/", "application/x-javascript", "application/javascript" )):
            filename = os.path.join(self._download_dir, md5(request["url"].encode()).hexdigest() + '.txt')        
            with open(filename, 'wb') as f:
                try:
                    f, headers = self._download_file(url=request["url"], destination=f)
                except requests.exceptions.SSLError:
                    try:
                        requests.packages.urllib3.disable_warnings()
                        f, headers = self._download_file(url=request["url"], destination=f, verify=False)
                    except Exception as e:
                        print("Error #1: %s" % (str(e)))
                except UnicodeError as e:
                    print("Error #2: Couldn't download url %s with error %s" % (request["url"], str(e)))
                except Exception as e:
                    print("Error #3: %s" % (str(e)))
                print("Found external resource %s. Saving file %s" % (request["url"], filename))
            if os.path.getsize(filename) == 0:
                os.remove(filename)
                print("Deleted file %s for it was empty!" % filename)

    def _get_network(self, log_entries):
        """ Reads the performance log entries and computes a network traffic dictionary based on the actual requests. """

        network_traffic = {}
        for log_entry in log_entries:
            message = jloads(log_entry["message"])
            method = message["message"]["method"]
            params = message["message"]["params"]
            if method not in ["Network.requestWillBeSent", "Network.responseReceived", "Network.loadingFinished"]:
                continue
            if method != "Network.loadingFinished":
                request_id = params["requestId"]
                loader_id = params["loaderId"]
                if loader_id not in network_traffic:
                    network_traffic[loader_id] = {"requests": {}, "encoded_data_length": 0}
                if request_id == loader_id:
                    if "redirectResponse" in params:
                        network_traffic[loader_id]["encoded_data_length"] += params["redirectResponse"]["encodedDataLength"]
                    if method == "Network.responseReceived":
                        network_traffic[loader_id]["type"] = params["type"]
                        network_traffic[loader_id]["url"] = params["response"]["url"]
                        network_traffic[loader_id]["remote_IP_address"] = None
                        if "remoteIPAddress" in params["response"].keys():
                            network_traffic[loader_id]["remote_IP_address"] = params["response"]["remoteIPAddress"]
                        network_traffic[loader_id]["encoded_data_length"] += params["response"]["encodedDataLength"]
                        network_traffic[loader_id]["headers"] = params["response"]["headers"]
                        network_traffic[loader_id]["status"] = params["response"]["status"]
                        network_traffic[loader_id]["security_state"] = params["response"]["securityState"]
                        network_traffic[loader_id]["mime_type"] = params["response"]["mimeType"]
                        if "via" in params["response"]["headers"]:
                            network_traffic[loader_id]["cached"] = True
                else:
                    if request_id not in network_traffic[loader_id]["requests"]:
                        network_traffic[loader_id]["requests"][request_id] = {"encoded_data_length": 0}
                    if "redirectResponse" in params:
                        network_traffic[loader_id]["requests"][request_id]["encoded_data_length"] += params["redirectResponse"]["encodedDataLength"]
                    if method == "Network.responseReceived":
                        network_traffic[loader_id]["requests"][request_id]["type"] = params["type"]
                        network_traffic[loader_id]["requests"][request_id]["url"] = params["response"]["url"]
                        network_traffic[loader_id]["requests"][request_id]["remote_IP_address"] = None
                        if "remoteIPAddress" in params["response"].keys():
                            network_traffic[loader_id]["requests"][request_id]["remote_IP_address"] = params["response"]["remoteIPAddress"]
                        network_traffic[loader_id]["requests"][request_id]["encoded_data_length"] += params["response"]["encodedDataLength"]
                        network_traffic[loader_id]["requests"][request_id]["headers"] = params["response"]["headers"]
                        network_traffic[loader_id]["requests"][request_id]["status"] = params["response"]["status"]
                        network_traffic[loader_id]["requests"][request_id]["security_state"] = params["response"]["securityState"]
                        network_traffic[loader_id]["requests"][request_id]["mime_type"] = params["response"]["mimeType"]
                        if "via" in params["response"]["headers"]:
                            network_traffic[loader_id]["requests"][request_id]["cached"] = 1
            else:
                request_id = params["requestId"]
                encoded_data_length = params["encodedDataLength"]
                for loader_id in network_traffic:
                    if request_id == loader_id:
                        network_traffic[loader_id]["encoded_data_length"] += encoded_data_length
                    elif request_id in network_traffic[loader_id]["requests"]:
                        network_traffic[loader_id]["requests"][request_id]["encoded_data_length"] += encoded_data_length
        return network_traffic

    def navigate_to(self, domain):
        print("Visit %s" % domain)
        
        
        # This might raise exception. it will be captured in Crawler Manager.
        self._driver.get("https://" + domain)
        sleep(10)
        # Get network traffic dictionary
        log_entries = self._driver.get_log('performance')
        network_traffic = self._get_network(log_entries)
        # Process traffic dictionary
        for key in network_traffic.keys():
            self.download_resources(domain, network_traffic[key])
            for sub_key in network_traffic[key]["requests"].keys():
                self.download_resources(domain, network_traffic[key]["requests"][sub_key])

             
    
    def visit_one(self, url):
        """Visits a website of the list if still in runs_per_site. 

        :param url: A string that represents the url of a domain.
        
        :returns: None.
        """
        # create dir for domain
        domain_dir = str(self._download_dir) + url.replace(".", "-") + os.path.sep
        os.makedirs(domain_dir, exist_ok=True)

        while self._current_run < self._runs_per_site:
            run_dir = domain_dir + str(self._current_run) + os.path.sep
            os.makedirs(run_dir, exist_ok=True)

            self.navigate_to(url)
            self.clear_data()
        
            # move all downloaded files to domain_dir/run_dir
            for f in os.listdir(self._download_dir):
                filename = self._download_dir + f
                if not os.path.isdir(filename):
                    os.rename(filename, run_dir + f)

            self._current_run = self._current_run + 1
   
        self._current_run = 0

    
    def visit_all(self, url_list):
        """Visits every website of the given list, if it hasn't been visited before. 

        :param url_list: A list of strings that represent the urls of a list of domains.
        
        :returns: None.
        """

        while self._current_url < len(url_list):
            ws = url_list[self._current_url]
            self.visit_one(ws)
            self._current_url = self._current_url + 1
        self._current_url = 0
    
    def close(self):
        """Closes the driver.
        
        :returns: None.
        """

        self._driver.close()

class CrawlerManager:
    def __init__(self, name, url_list, runs=1, extension=None, current_url=0, current_run=0):
        self._name = name
        self._url_list = url_list
        self._crawler = Crawler(runs, extension, current_url, current_run)

        # Workaround to activate extensions
        wait = True
        while wait:
            wait = input("Start? [y/n]: ") != "y"

        self.run()

    def run(self):
        try:
            self._crawler.visit_all(self._url_list)
        except Exception as e:
            print("Error: %s" % e)
            traceback.print_exc()
            self._crawler.close()
            
            self._crawler = Crawler(
                runs=self._crawler._runs_per_site, 
                extension=self._crawler._extension,
                current_url=self._crawler._current_url+1, 
                current_run=self._crawler._current_run)
            wait = True
            while wait:
                wait = input("Start? [y/n]: ") != "y"
            self.run()

    



