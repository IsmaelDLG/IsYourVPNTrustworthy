import sys
import os

_START_TAG = b"<script"
_END_TAG = b"</script>"

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

for dir in dir_list:
    for filename in os.listdir(dir):
        print("Check file %s" % dir + os.path.sep + filename)
        with open("%s-%s.%s" % (out_name, dir[:-1], out_ext), 'a') as ffd:
                        ffd.write("##########%s##########\n" % filename)
        with open(os.path.abspath(dir) + os.path.sep + filename, 'rb') as fd:
            line = fd.readline()
            beg = end = None
            count = 0
            while line != b"":
                if beg is None:
                    beg = line.find(_START_TAG)
                    if beg == -1:
                        beg = None 
                if beg is not None:
                    end = line.find(_END_TAG)
                    if end == -1:
                        end = None
                if beg is not None and end is not None:
                    last = fd.tell()
                    fd.seek(count + beg,0)
                    target = fd.read(end-beg + len(_END_TAG))
                    fd.seek(last, 0)
                    with open("%s-%s.%s" % (out_name, dir[:-1], out_ext), 'a') as ffd:
                        ffd.write(target.decode() + '\n' + '#'*10 + '\n')
                    beg = end = None
                count = count + len(line)
                line = fd.readline()