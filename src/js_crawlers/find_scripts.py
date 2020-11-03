import sys
import os
import time
from bs4 import BeautifulSoup
import json

if len(sys.argv) < 2 or not (os.path.exists(sys.argv[1])):
    print("")
    print("usage: find_scripts.py <folder1> ... [-o out_file]")
    exit(1)

args = sys.argv[1:]

# Get output file
if sys.argv[-2] == "-o":
    out = sys.argv[-1]
    args = sys.argv[1:-3]
else:
    out = os.path.abspath(os.curdir) + os.path.sep + "out.txt"

out_name, out_ext = out.split('.')

# Get input dirs
dir_list = []
for dir in args:
    if os.path.exists(dir):
        dir_list.append(dir)
    else:
        raise FileNotFoundError("Could not find input directory %s!" % dir)

# Get Scripts and IFrames
result = {}
for dir in dir_list:
    for filename in os.listdir(dir):
        
        if result.get(filename, None) is None:
            result[filename] = {}

        with open(os.path.abspath(dir) + os.path.sep + filename, 'r') as fd:
            soup = BeautifulSoup(fd.read(), 'html.parser')
            scripts = []
            [scripts.append(str(x)) for x in soup.find_all('script')]
            iframes = []
            [iframes.append(str(x)) for x in soup.find_all('iframe')]
            result[filename][dir] = {}
            result[filename][dir]['scripts'] = scripts
            result[filename][dir]['iframes'] = iframes

# Check if everyone has the same scripts
for name in result:
    equal = True
    last = None
    for dir in result[name]:
        if last is not None:
            equal = (last == result[name][dir])
        else:
            last = result[name][dir]

    result[name]["equal"] = equal

with open ("%s-%i.json" % ("&".join(dir_list), time.time()), 'w') as f:
    json.dump(result, f, indent=4)