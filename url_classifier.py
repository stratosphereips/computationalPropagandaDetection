import importlib
from models.create_graph import get_graph
from models.utils import *

import argparse
import pickle
wnm = importlib.import_module("web-network-mapper")


def add_node_embedding(dataset):
    no_time_flag = 0
    g = dataset
    levels = np.zeros(3)
    snas = np.zeros((len(g.nodes), 5))
    time_diffs = []
    for i in range(len(g.nodes)):
        n = g.nodes[i]
        g.nodes[i]['h'] = torch.tensor([
            0., 0., 0.,  # one hot level encoding
            n['time_diff'], n['no_time'],
            *n['sna']
        ])
        snas[i] = n['sna']
        levels[g.nodes[i]['level']] += 1
        if n['no_time'] != 1:
            time_diffs.append(n['time_diff'])
        else:
            no_time_flag += 1
    links = 0
    titles = 0
    domain = 0
    for e in g.edges:
        if g.edges[e]['link_type'] == 'link':
            links += 1

        if g.edges[e]['link_type'] == 'title':
            titles += 1
        if g.edges[e]['link_type'] == 'domain':
            domain += 0.5

    levels /= len(g.nodes)
    time_diff_mean = np.asarray(time_diffs).mean()
    time_diff_std = np.asarray(time_diffs).std()
    no_time_flag /= len(g.nodes)

    mean_sna = snas.mean(0)

    fv = np.array([*levels, time_diff_mean, time_diff_std, no_time_flag, *mean_sna, len(g.nodes), len(g.edges),
                   links / (links + titles), domain / len(g.nodes)])
    return fv

def main(url, db_path):
    print("Running the Werge")
    wnm.main(url, is_propaganda=False, database="DB/DB/databases/propaganda.db", verbosity=0, number_of_levels=2,
             urls_threshold=0.3, max_results=100)
    print("Werge finished")
    nx_graph = get_graph(db_path, main_url=url)
    nx_graph = add_domain([nx_graph])[0]
    nx_graph = add_time_difference([nx_graph])[0]
    nx_graph = add_sna([nx_graph])[0]
    nx_graph = all_node_embedding(nx_graph)
    fv = [add_node_embedding(nx_graph)]

    with open('model.pickle', 'rb') as f:
        model = pickle.load(f)

    prediction = model.predict(fv)
    probability = model.predict_proba(fv)[0][prediction][0]
    if prediction == 1:
        print("Questioned URL is PROPAGANDA with probability {:.2f}%".format(100*probability))
    else:
        print("Questioned URL is NON-PROPAGANDA with probability {:.2f}%".format(100*probability))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-u", "--url", help="URL of artice to be classified.", type=str, required=False, default="https://www.pythontutorial.net/python-basics/python-directory/"
    )
    parser.add_argument(
        "-db", "--database_path", help="Path to database file, db is created if not exist, however folder structure must exist",
        default='propaganda.db', type=str
    )
    args = parser.parse_args()


    url='https://oroszhirek.hu/2021/11/30/hoppa-oroszorszag-es-kina-osszefog-az-illegitim-amerikai-szankciok-ellen/'
    db_path='C:\propaganda\computationalPropagandaDetection\dataset\propaganda\propaganda_1.db'

    main(url, db_path)
    # main(args.url, args.database_path)