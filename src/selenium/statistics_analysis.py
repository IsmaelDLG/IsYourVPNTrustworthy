import statistics
import json

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

INPUT_DIR=Path('./').absolute()

def desviation(a_list):
    return statistics.stdev(a_list)

def make_barplot(desv_dicc):
    keys = []
    values = []
    for key, value in desv_dicc.items():
        keys.append(key)
        values.append(value)
    plt.bar(keys, values)
    plt.xticks(rotation=45)
    plt.show()

if __name__ == '__main__':
    with open('analysis01_short.json', 'r') as f:
        data01 = json.load(f)
    the_lists01 = {}
    for ext in data01:
        for f in data01[ext]:
            if f in the_lists01:
                the_lists01[f].append(data01[ext][f])
            else:
                the_lists01[f] = [data01[ext][f]]
    
    # Get std desviation
    for f in the_lists01:
        if len(the_lists01[f]) > 1:
            the_lists01[f] = desviation(the_lists01[f])
        else:
            the_lists01[f] = 0

    # make_barplot(the_lists01)
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
