from datasketch import MinHash, MinHashLSH
import sys, os, json, time

INPUT_DIR = "C:\\Users\\ismae\\Downloads"
HASHER = minhash.MinHasher(seeds=1000, char_ngram=5)

NUM_PERM = 128
THRESHOLD = 0.5

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
    
    with open(filename, 'rb', encoding=encode) as fd:
        if granularity == 0:
            res = fd.readlines()
        elif:
            aux = fd.read()
            # Appends items to the res list using the given granularity
            [res.append(aux[i:i+granularity-1]) for i in range(0, len(aux), granularity)]
    
    return set(res)

def create_minhash(a_set, perms=PERMUTATIONS):
    """Returns a minhash of the given set using the permutation number given.
    """

    a_minhash = MinHash(num_perm=NUM_PERM)

    for group in a_set:
        a_minhash.update(group)

    return a_minhash

def compare(minhash_list):
    """Returns the similarity betweeen the differents sets, using the Jaccard algorithm.
    """
    




if __name__ == '__main__':
    short_opts = "hd:"
    long_opts = ["help", "directory="]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        _usage()

    if len(args) < 1:
        _usage()
    
    for opt, arg in opts:
        if opt in ('-h', '--help') :
            _usage()
        elif opt in ('-d', '--directory'):
            try:
                INPUT_DIR = str(Path(arg).absolute())            
            except:
                _usage()
    
    

            

    
