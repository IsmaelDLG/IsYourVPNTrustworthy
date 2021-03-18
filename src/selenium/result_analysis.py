import statistics
import json
import os
import sys
import copy
from time import time
from math import ceil


from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import NullFormatter

from getopt import getopt, GetoptError



_INPUT_FILE=Path('./metadata_analysis.json')
_REP_TRESHOLD = 0.80


# FILE ANALYSIS

def _repetitions(webpage_tree):
    """Finds metadata on resources are present in the different runs of the webpages, using the treshold. 
    Also orders the data in a logical way and returns 2 dictionaries, one of metadata and one of data."""
    
    metadata = {
        "runs" : len(webpage_tree),
        "max_resources_run": 0,
        # a huge number
        "min_resources_run": time() * 99999,
        "avg_resources_run": 0,
        "static_resources": 0,
        "dynamic_resources": 0,
        "files" : {},
    }
    data = {}

    if len(webpage_tree) > 0:
        for run in webpage_tree:
            files_in_run = len(webpage_tree[run])
            if metadata["min_resources_run"] > files_in_run:
                metadata["min_resources_run"] = files_in_run
            if metadata["max_resources_run"] < files_in_run:
                metadata["max_resources_run"] = files_in_run
            metadata["avg_resources_run"] = metadata["avg_resources_run"] + files_in_run
            for f in webpage_tree[run]:
                filename = f.split(os.path.sep)[-1]
                if filename not in data:
                    metadata["files"][filename] = {
                        "reps": 1,
                    }
                    data[filename] = {
                        "reps": 1,
                        "hash": webpage_tree[run][f],
                    }
                else:
                    metadata["files"][filename]["reps"] = metadata["files"][filename]["reps"] + 1
                    data[filename]["reps"] = data[filename]["reps"] + 1

        metadata["avg_resources_run"] = int(metadata["avg_resources_run"] / metadata["runs"])

        for f in data:
            if metadata["files"][f]["reps"] >= (metadata["runs"] * _REP_TRESHOLD):
                metadata["static_resources"] = metadata["static_resources"] + metadata["files"][f]["reps"]
            else:
                metadata["dynamic_resources"] = metadata["dynamic_resources"] + metadata["files"][f]["reps"]

    return metadata, data

def repetitions_analysis(tree, selector=None):
    """Gets repetition data for all results. If selector is set, it indicates which 
    trees should be visited. selector is a list of strings that ndicate the name of
    the root of each tree."""
    
    metadata = {}
    data = {}
    for extension_dir in tree:
        if selector:
            if extension_dir not in selector:
                continue
        extension = extension_dir.split(os.path.sep)[-1]
        metadata[extension] = {}
        data[extension] = {}
        for webpage_dir in tree[extension_dir]:
            webpage = webpage_dir.split(os.path.sep)[-1]
            metadata[extension][webpage], data[extension][webpage] = _repetitions(tree[extension_dir][webpage_dir])
    return metadata, data

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

def find_similarities(data):
    """Find similarity of each file with the files present in the webpage with no vpn."""

    good_one = copy.deepcopy(data["no_vpn"])
    del data["no_vpn"]

    all_minhashes = []
    
    # put everything easy to work with
    for extension in data:
        for webpage in data[extension]:
            for f in data[extension][webpage]:
                path = (extension, webpage, f)
                all_minhashes.append((path, data[extension][webpage][f]))
    aux = copy.deepcopy(all_minhashes)
    path_data, data = aux.pop(0)
    all_minhashes.pop(0)

    result = {}
    while path_data and data:
        for file in good_one[path_data[1]]:
            # print("Jaccard among %s and %s" % (path_data[2], file))
            path_to_file = "/".join(("no_vpn", path_data[1], file))
            similarity = data["hash"].jaccard(good_one[path_data[1]][file]["hash"])
            try:
                result["/".join(path_data)].append((path_to_file, similarity))
            except KeyError:
                result["/".join(path_data)] = [(path_to_file, similarity),]

        all_minhashes.append((path_data, data))
        try:
            path_data, data = aux.pop(0)
        except IndexError:
            path_data = data = None

    return result

def find_uniques(data, similarity_treshold=0.8):
    """Deletes entries if they have similarity_treshold or higher with at least one file of the site without a vpn active."""

    res = {}

    for key, value in list(data.items()):
        if any(x >= similarity_treshold for k, x in value):
            del data[key]
            continue
        else:
            # A self defined max function for the occasion
            current_max = 0.0
            current_file = None
            for path, sim in value:
                if sim > current_max:
                    current_max = sim
                    current_file = path

            res[key] = { 
                "max_similarity":current_max,
                "file": current_file
                }
    
    return res

def desviation(a_list):
    return statistics.stdev(a_list)

# PLOTS

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

def _format_plot(x_title = None, y_title = None, x_label_rot = None, y_label_rot = None, x_labels = None, y_labels = None, title = None):
    if title:
        plt.title(title)
    if x_title:
        plt.xlabel = x_title
    if y_title:
        plt.ylabel = y_title
    if x_label_rot:
        plt.xticks(rotation=x_label_rot)
    if y_label_rot:
        plt.yticks(rotation=y_label_rot)

def make_bar_plot(x_axis, y_axis, x_title = None, y_title = None, x_label_rot = None, y_label_rot = None, x_labels = None, y_labels = None, title = None):
    plt.bar(x_axis, y_axis)

    _format_plot(x_title, y_title, x_label_rot, y_label_rot, x_labels, y_labels, title)

    plt.show()

def make_group_bar_plot(x_axis, y_axis, x_title = None, y_title = None, x_label_rot = None, y_label_rot = None, x_labels = None, y_labels = None, title = None):
    fig, ax = plt.subplots(figsize=(12, 8))

    bar_width = float(0.1)
    x = np.arange(len(x_axis))

    acc = 0
    for data in y_axis:
        a_bar = ax.bar([val + acc for val in x], data, width=bar_width)
        acc = acc + bar_width

    # Fix the x-axes.
    ax.set_xticks([val + bar_width*2/3 for val in x])
    ax.set_xticklabels(x_axis)

    _format_plot(x_title, y_title, x_label_rot, y_label_rot, x_labels, y_labels, title)

    # Axis styling.
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#DDDDDD')
    ax.tick_params(bottom=False, left=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color='#EEEEEE')
    ax.xaxis.grid(False)
    # Add axis and chart labels.
    ax.set_xlabel(x_title, labelpad=15)
    ax.set_ylabel(y_title, labelpad=15)
    fig.tight_layout()

    plt.show()

if __name__ == '__main__':
    
    short_opts = "hf:"
    long_opts = ["help","metadata-file="]

    try:
        opts, args = getopt(sys.argv[1:], short_opts, long_opts)
    except Exception:
        _usage()
    
    for opt, arg in opts:
        if opt in ('-h', '--help') :
            _usage()
        elif opt in ('-f', '--metadata-file'):
            _INPUT_FILE = Path(arg).absolute()
    
    with open(_INPUT_FILE, 'r') as f:
        data = json.load(f)
    

    static_resource_data = {}
    dynamic_resource_data = {}
    total_resource_data = {}
    
    for extension in data:
        for webpage in data[extension]:
            if webpage not in static_resource_data:
                static_resource_data[webpage] = {
                    "keys": [extension,],
                    "values": [ceil(data[extension][webpage]["static_resources"] / data[extension][webpage]["runs"]),]
                }
                dynamic_resource_data[webpage] = {
                    "keys": [extension,],
                    "values": [ceil(data[extension][webpage]["dynamic_resources"] / data[extension][webpage]["runs"]),]
                }
                total_resource_data[webpage] = {
                    "keys": [extension,],
                    "values": [
                        [data[extension][webpage]["min_resources_run"],],
                        [data[extension][webpage]["max_resources_run"],],
                        [data[extension][webpage]["avg_resources_run"],],
                    ]
                }
            else:
                static_resource_data[webpage]["keys"].append(extension)
                try:
                        static_resource_data[webpage]["values"].append(ceil(data[extension][webpage]["static_resources"] / data[extension][webpage]["runs"]))
                except ZeroDivisionError:
                        static_resource_data[webpage]["values"].append(0)

                dynamic_resource_data[webpage]["keys"].append(extension)
                try:
                        dynamic_resource_data[webpage]["values"].append(ceil(data[extension][webpage]["dynamic_resources"] / data[extension][webpage]["runs"]))
                except ZeroDivisionError:
                        dynamic_resource_data[webpage]["values"].append(0)

                total_resource_data[webpage]["keys"].append(extension)
                total_resource_data[webpage]["values"][0].append(data[extension][webpage]["min_resources_run"])
                total_resource_data[webpage]["values"][1].append(data[extension][webpage]["max_resources_run"])
                total_resource_data[webpage]["values"][2].append(data[extension][webpage]["avg_resources_run"])

    """
    for webpage in static_resource_data:
        make_bar_plot(
            static_resource_data[webpage]["keys"],
            static_resource_data[webpage]["values"],
            x_title="Extension Used",
            y_title="Nº of static resources per run",
            title="Static resources (presence >= treshhold * runs) found in webpage %s using different VPN extensions." % webpage
        )

    for webpage in dynamic_resource_data:
        make_bar_plot(
            dynamic_resource_data[webpage]["keys"],
            dynamic_resource_data[webpage]["values"],
            x_title="Extension Used",
            y_title="Nº of dynamic resources per run",
            title="Dynamic resources (presence < treshhold * runs) found in webpage %s using different VPN extensions." % webpage
        )
    """
    for webpage in static_resource_data:
        make_group_bar_plot(
            total_resource_data[webpage]["keys"],
            total_resource_data[webpage]["values"],
            x_title="Extension Used",
            y_title="# of MIN/MAX/AVG resources per run",
            title="Resources found in webpage %s using different VPN extensions." % webpage
        )




