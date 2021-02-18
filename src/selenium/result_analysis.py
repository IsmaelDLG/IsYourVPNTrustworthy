import statistics
import json
import os
import copy


from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter


INPUT_DIR=Path('./').absolute()

def _repetitions(webpage_tree):
    """Finds how many times resources are present in the different runs of the webpages, using the treshold."""
    
    if len(webpage_tree) > 0:
        result = {
            "runs" : len(webpage_tree)
        }
        for run in webpage_tree:
            for f in webpage_tree[run]:
                filename = f.split(os.path.sep)[-1]
                if filename not in result:
                    result[filename] = {
                        "reps": 1,
                        "hash": webpage_tree[run][f],
                    }
                else:
                    result[filename]["reps"] = result[filename]["reps"] + 1
        
        # sorts dictionary descendant according to repetitions
        # Doesn't work
        # result = {key: value for key, value in sorted(result.items(), key=lambda item: item[1], reverse=True)}

    return result

def repetitions(tree):
    """Gets repetition data for all results."""
    
    res = {}
    for extension_dir in tree:
        extension = extension_dir.split(os.path.sep)[-1]
        res[extension] = {}
        for webpage_dir in tree[extension_dir]:
            webpage = webpage_dir.split(os.path.sep)[-1]
            res[extension][webpage] = _repetitions(tree[extension_dir][webpage_dir])
    return res

def discard_resources(data, presence_treshold=1.0):
    """This method discard resources present in the \"no_vpn\" dictionary, 
    for they are 100% not vpn-dependant."""
    
    # we will discard stuff from this copy
    res = copy.deepcopy(data)
    
    # to compare easier
    good_one = copy.deepcopy(data["no_vpn"])
    del data["no_vpn"]


    to_del = []

    for extension in data:
        for webpage in data[extension]:
            for f in data[extension][webpage]:
                if f in ("runs",):
                    continue
                # if case["reps"] >= (runs*treshold):
                if f in good_one[webpage]:
                    del res[extension][webpage][f]
                    # this will repeat, but it shouldn't be a problem
                    to_del.append((webpage, f))

    for webpage, file in to_del:
        try:
            del data["no_vpn"][webpage][file]
        except KeyError:
            pass
        
    return res

def find_similarities(data, similarity_treshold=0.8):
    """For each file, find all files with high similarity."""

    good_one = copy.deepcopy(data["no_vpn"])
    del data["no_vpn"]
    
    all_minhashes = []

    # put everything easy to work with
    for extension in data:
        for webpage in data[extension]:
            for file in data[extension][webpage]:
                path = (extension, webpage, file)
                all_minhashes.append((path, data[extension][webpage][file]))

    aux = copy.deepcopy(all_minhashes)
    path_data, data = aux.pop(0)
    all_minhashes.pop(0)
    while path_data and data:
        for comp_path, comp_data in all_minhashes:
            similarity = data["hash"].jaccard(comp_data["hash"])
            if similarity >=similarity_treshold:
                        
        
        all_minhashes.append((path_data, data))
        try:
            path_data, data = aux.pop(0)
        except IndexError:
            path_data = data = None

    print("Finished!")
    print(all_minhashes)

def desviation(a_list):
    return statistics.stdev(a_list)

def make_barplot(title, desv_dicc):
    keys = []
    values = []
    for key, value in desv_dicc.items():
        keys.append(key)
        values.append(value)
    plt.bar(keys, values)
    plt.title(title)
    plt.xticks(rotation=45)
    plt.show()

if __name__ == '__main__':
    with open('C:\\Users\\ismae\\Downloads\\analysis01_short.json', 'r') as f:
        data01 = json.load(f)
    stdv_webpages = {}
    for ext in data01:
        for f in data01[ext]:
            if f in stdv_webpages:
                stdv_webpages[f].append(data01[ext][f])
            else:
                stdv_webpages[f] = [data01[ext][f],]
    
    for f in stdv_webpages:
        if len(stdv_webpages[f]) > 1:
            stdv_webpages[f] = desviation(stdv_webpages[f])
        else:
            stdv_webpages[f] = 0
    
    make_barplot("Standard deviation in similarity of the webpages among different VPNs", stdv_webpages)
    
    with open('C:\\Users\\ismae\\Downloads\\analysis01_full.json', 'r') as f:
        data02 = json.load(f)
    
    similarity_per_vpn_per_page = {}
    for ext in data02:
        similarity_per_vpn_per_page[ext] = {}
        for group in data02[ext]:
            values = []
            for run in data02[ext][group]:
                values.append(data02[ext][group][run])
            if len(values) >= 1:
                similarity_per_vpn_per_page[ext][group] = sum(values) / len(values)
            else:
                similarity_per_vpn_per_page[ext][group] = 0
        make_barplot("Similarity of wepages in VPN %s" % ext, similarity_per_vpn_per_page[ext])

    deviation_per_vpn_per_page = {}
    for ext in data02:
        deviation_per_vpn_per_page[ext] = {}
        for group in data02[ext]:
            values = []
            for run in data02[ext][group]:
                values.append(data02[ext][group][run])
            if len(values) > 1:
                deviation_per_vpn_per_page[ext][group] = desviation(values)
            else:
                deviation_per_vpn_per_page[ext][group] = 0
        make_barplot("Standard deviation in similarity of wepages in VPN %s" % ext, deviation_per_vpn_per_page[ext])
    
    
            



    """
    with open('analysis02.json', 'r') as f:
        data02 = json.load(f)
    for ext in data02:
        semblanca = []
        for key, value in data02[ext].items():
            semblanca.append(value)
        
        avg = 0
        for x in semblanca:
            avg = avg + x 
        data02[ext] = avg / (len(semblanca) if len(semblanca) > 0 else 1)
    
    make_barplot(data02)
    """