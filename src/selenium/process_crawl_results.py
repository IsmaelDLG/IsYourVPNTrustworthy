from datasketch import MinHash, MinHashLSH
from pathlib import Path
from getopt import getopt, GetoptError

import sys, os, json, time

INPUT_DIR = "C:\\Users\\ismae\\Downloads\\test"

NUM_PERM = 4096

def _usage():
    print("\tusage: {file} [-h|d <directory>]".format(file=__file__))
    sys.exit(2)

def create_set(filename, granularity=0, encode="utf8"):
    """Creates a set for to use in a MinHash from the given filename. 
    Splits the file in groups of characters according to the given 
    granularity (0 means each group represents a line of the file). 
    Uses given encoding.
    """

    res = []
    
    with open(filename, 'rb') as fd:
        if granularity == 0:
            res = fd.readlines()
        else:
            aux = fd.read()
            # Appends items to the res list using the given granularity
            [res.append(aux[i:i+granularity-1]) for i in range(0, len(aux), granularity)]
    
    return (filename, set(res))

def create_minhash(a_set, perms=NUM_PERM):
    """Returns a minhash of the given set using the permutation number given.
    """

    a_minhash = MinHash(num_perm=perms)

    for group in a_set:
        a_minhash.update(group)

    # print(a_minhash.digest())
    
    return a_minhash

def compare_single(minhash_dic):
    """Returns a list with the jaccard similarity of the sets with the rest of the neighbours.
    """
    
    res = {}
    for target in minhash_dic:
        aux = minhash_dic.copy()
        aux.pop(target)
        counter = 1
        avg = 0
        for neighbour in aux:
            avg = avg + minhash_dic[target].jaccard(aux[neighbour])
            counter = counter + 1
        avg = avg / counter
        res[target] = avg
    
    return res
    


def compare_merged(minhash_list):
    """Returns a the jaccard similarity of the sets.
    """
    
    jaccards = compare_single(minhash_list)
    avg = 0
    for x in jaccards:
        avg = avg + x
    return avg / len(jaccards)


if __name__ == '__main__':
    short_opts = "hd:"
    long_opts = ["help", "directory="]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        print("Couldn't get options!")
        _usage()
    
    for opt, val in opts:
        if opt in ('-h', '--help') :
            _usage()
        elif opt in ('-d', '--directory'):
            try:
                INPUT_DIR = str(Path(val).absolute())            
            except:
                _usage()
    
    if os.path.exists(INPUT_DIR):
        minhash_dic = {}
        for file in os.listdir(INPUT_DIR):
            filename, a_set = create_set(INPUT_DIR + os.path.sep + file)
            mh = create_minhash(a_set)
            minhash_dic[filename] = mh
        import json
        print(json.dumps(compare_single(minhash_dic), indent=4))
    
    

            

    
