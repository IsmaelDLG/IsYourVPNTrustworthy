import statistics
import json

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter

INPUT_DIR=Path('./').absolute()

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