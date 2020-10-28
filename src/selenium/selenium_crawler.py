import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

exe_path = "./chromedriver"
os.environ["webdriver.chrome.driver"] = exe_path

chrome_options = Options()
chrome_options.add_extension('./extension/download_page.js')

driver = webdriver.Chrome(executable_path=exe_path, chrome_options=chrome_options)
driver.get("http://www.python.org")
# assert "Python" in driver.title
# elem = driver.find_element_by_name("q")
# elem.clear()
# elem.send_keys("pycon")
# elem.send_keys(Keys.RETURN)
# assert "No results found." not in driver.page_source
# driver.close()
