from lsh import minhash
import sys, os, json, time

INPUT_DIR = "C:\\Users\\ismae\\Downloads"
HASHER = minhash.MinHasher(seeds=1000, char_ngram=5)

def _usage():
    print("\tusage: {file} [-h|d <directory>]".format(file=__file__))
    sys.exit(2)

def hash_file(str_path):
    """Makes the hash of the given file.
    """
    text = b""
    try:
        with open(str_path, 'rb') as fd:
            text = fd.read()
    except:
        print("Error with file %s" % str_path)

    return HASHER.fingerprint(text)

def compare(hash1, hash2):
    """Compares two hashes and returns the similarity.
    """
    return sum(hash1[i] in hash2 for i in range(HASHER.num_seeds)) / HASHER.num_seeds


def compare_hash(target, others):
    """Compares the target hash with the rest of the documents, and returns a dic of the similarity for each hash.
    """
    ret = {}
    for sample in others:
        ret[sample] = compare(target, sample)
    return ret


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
    
    hash_list = []
    json_result = {}
    for comparable in os.listdir(INPUT_DIR):
        filename = INPUT_DIR + os.path.sep + comparable
        a_hash = hash_file(filename)
        json_result[a_hash] = {}
        json_result[a_hash]["filename"] = filename
        hash_list.append(a_hash)
    
    for h in hash_list:
        json_result[h]["comparisons"] = compare_hash(h, hash_list.remove(h))

    with open (INPUT_DIR + os.path.sep + "result-%i.json" % int(time.time()), 'r') as fd:
         json.dump(json_result, fd, indent=2)

            

    
