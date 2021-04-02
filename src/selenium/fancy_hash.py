from datasketch import MinHash, MinHashLSH
from pathlib import Path
from getopt import getopt, GetoptError

import sys, os, json, time

INPUT_DIR = "/home/ismael/Downloads/"

NUM_PERM = 230
# 0 is whole line
JACC_GRANULARITY = 0


def _usage():
    print("\tusage: {file} [-h|d <directory>]".format(file=__file__))
    sys.exit(2)


def _create_set(filename, granularity=JACC_GRANULARITY):
    """Creates a set for to use in a MinHash from the given filename.
    Splits the file in groups of characters according to the given
    granularity (0 means each group represents a line of the file).
    """

    res = []

    with open(filename, "rb") as fd:
        if granularity == 0:
            res = fd.readlines()
        else:
            aux = fd.read()
            # Appends items to the res list using the given granularity
            [
                res.append(aux[i : i + granularity - 1])
                for i in range(0, len(aux), granularity)
            ]

    return set(res)


def _create_minhash(a_set, perms=NUM_PERM):
    """Returns a minhash of the given set using the permutation number given."""

    a_minhash = MinHash(num_perm=perms)

    for group in a_set:
        a_minhash.update(group)

    # print(a_minhash.digest())

    return a_minhash


def _compare_single(minhash_dic):
    """Returns a dictionary (filename, similarity), with the jaccard similarity of the Minhashes with the rest of the neighbours."""

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


def _compare_merged(minhash_dic):
    """Returns a the jaccard similarity of the minhashes."""

    jaccards = _compare_single(minhash_dic)
    avg = 0
    for x in jaccards:
        avg = avg + jaccards[x]
    try:
        ret = avg / len(jaccards)
    except:
        ret = 0

    return ret


def calc_proximity_of_dir(a_dir=INPUT_DIR):
    """Calculate proximit between files, assuming all the files are in a_dir."""

    res = None
    if os.path.isdir(a_dir):
        minhash_dic = {}
        for file in os.listdir(a_dir):
            filename, a_set = _create_set(a_dir + os.path.sep + file)
            mh = _create_minhash(a_set)
            minhash_dic[filename] = mh
        res = _compare_single(minhash_dic)
    return (_compare_merged(minhash_dic), res)


def _get_all_mh(a_dir):
    files = {}
    if os.path.isdir(a_dir):
        for root in os.listdir(a_dir):
            # Case dir
            files[root] = {}
            case = a_dir + os.path.sep + root
            if not os.path.isdir(case):
                continue
            for f in os.listdir(case):
                # File dir
                fl = case + os.path.sep + f
                if not f.startswith("file-"):
                    continue
                elif not os.path.isdir(fl):
                    continue
                for script_file in os.listdir(fl):
                    a_file = fl + os.path.sep + script_file
                    print("Hashing file %s ..." % (a_file))
                    if f in files[root]:
                        # Update minhash with this one aswell
                        filename, a_set = _create_set(a_file)
                        a_mh = _create_minhash(a_set)
                        files[root][f].merge(a_mh)
                    else:
                        # Create minhash
                        filename, a_set = _create_set(a_file)
                        files[root][f] = _create_minhash(a_set)
    return files


def calc_proximity_two(a_dir=INPUT_DIR):
    minhashes_all = _get_all_mh(a_dir)
    result = {}
    for root in minhashes_all:
        if root == "no_vpn":
            continue
        result[root] = {}
        for mh in minhashes_all[root]:
            try:
                result[root][mh] = minhashes_all[root][mh].jaccard(
                    minhashes_all["no_vpn"][mh]
                )
            except KeyError:
                continue
    return result


def create_tree(a_dir=INPUT_DIR, created=[]):
    """Recursively loads all files in thee hierarchy as MH."""
    files = os.listdir(a_dir)
    result = {}
    for f in files:
        a_file = a_dir + os.path.sep + f
        # print("Loading file %s" % a_file)
        if os.path.isdir(a_file):
            result[a_file] = create_tree(a_file)
        elif os.path.isfile(a_file):
            # print("Using stub")
            # result[a_file] = "a_hash"
            result[a_file] = _create_minhash(_create_set(a_file))
    return result


if __name__ == "__main__":
    short_opts = "hd:"
    long_opts = ["help", "directory="]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        print("Couldn't get options!")
        _usage()

    for opt, val in opts:
        if opt in ("-h", "--help"):
            _usage()
        elif opt in ("-d", "--directory"):
            try:
                INPUT_DIR = str(Path(val).absolute())
            except:
                _usage()

    print("Analysis 01")
    print(calc_proximity_one())
    print("Analysis 02")
    print(calc_proximity_two())
