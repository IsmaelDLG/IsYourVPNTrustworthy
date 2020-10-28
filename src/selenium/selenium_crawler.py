import os, zipfile

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from pathlib import Path

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
# chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.experimental_options["useAutomationExtension"] = False

driver = webdriver.Chrome(executable_path=exe_path, options=chrome_options)
driver.get("http://www.python.org")



# assert "Python" in driver.title
# elem = driver.find_element_by_name("q")
# elem.clear()
# elem.send_keys("pycon")
# elem.send_keys(Keys.RETURN)
# assert "No results found." not in driver.page_source
# driver.close()
