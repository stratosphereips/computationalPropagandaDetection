import networkx as nx
import numpy as np
from DB.propaganda_db import DB
from create_features import *
from os import listdir
from os.path import isfile, join
import pickle
from sklearn.model_selection import train_test_split

import matplotlib.pyplot as plt

import dgl


def filter_name(url):
    if "http" in url:
        basename = url.split("/")[2]
    else:
        basename = url.split(" ")[0]
        pass
    if "www" == basename[:3]:
        return basename[4:]
    return basename


def get_graph(db_path, domain=False):
    domain = False
    db = DB(db_path)
    urls = db.get_url_by_id(1)[0][0]
    cur_edges, cur_nodes = db.get_tree(urls)

    new_nodes = [(node, (*cur_nodes[node], filter_name(node))) for node in cur_nodes]
    new_edges = [((referenced_by, url), edge_type) for _, url, referenced_by, edge_type
                 in cur_edges]
    if len(new_edges) <= 1:
        return None
    n2i = dict()
    i2n = dict()
    ctr = 0
    if domain:
        new_nodes = [(filter_name(n), attrs) for n, attrs in new_nodes]
    for n, _ in new_nodes:
        if n not in n2i:
            n2i[n] = ctr
            i2n[ctr] = n
            ctr += 1

    G = nx.MultiDiGraph()
    for n, attrs in new_nodes:
        G.add_node(n2i[n], publication_date=attrs[0], level=attrs[1], domain=attrs[2], url=n)
    used_edges = dict()
    for (f, t), link_type in new_edges:
        if domain:
            f = filter_name(f)
            t = filter_name(t)

        f = n2i[f]
        t = n2i[t]

        # there can be multiple edges from f to t found by title. This can happen because it was found by more engines (google, bing..)
        # we stored this only for the non-propaganda part, propaganda part was downloaded before this was introduced
        # it is therefore needed to add the link only once
        if (f,t) not in used_edges.keys() or link_type not in used_edges[f, t]:
            if link_type == 'link':
                G.add_edge(f, t, link=1, link_type='link')
            elif link_type == 'title':
                G.add_edge(f, t, title=1, link_type='title')
            else:
                raise Exception(f"Unknown link type {link_type}")

            if (f, t) not in used_edges.keys():
                used_edges[(f, t)] = {link_type}
            else:
                used_edges[(f,t)].add(link_type)



    return G


def get_graph_sna_feature_vector(graph):
    if graph is None:
        return np.zeros(9)
    in_degree = nx.algorithms.in_degree_centrality(graph)
    out_degree = nx.algorithms.out_degree_centrality(graph)
    betweenness = nx.algorithms.betweenness_centrality(graph)

    closeness = nx.algorithms.closeness_centrality(graph)
    eig = nx.algorithms.eigenvector_centrality(graph, max_iter=10000)
    undirected_graph = graph.to_undirected()
    # clustering
    clustering = nx.algorithms.clustering(graph)
    radius = nx.algorithms.distance_measures.radius(undirected_graph)
    n = len(in_degree)

    transitivity = nx.algorithms.transitivity(graph)

    edge_types = [n[-1]["edge_type"] for n in graph.edges(data=True)]

    link_num = edge_types.count("link")
    features = np.asarray([sum(closeness.values()) / n, sum(in_degree.values()) / n, sum(out_degree.values()) / n,
                           sum(betweenness.values()) / n, sum(eig.values()) / n, sum(clustering.values()) / n,
                           transitivity, radius, link_num / max(1, len(edge_types)), n, graph.number_of_edges()])

    return list(features)


def get_graph_time_vector(db_path):
    db = DB(db_path)
    main_url = db.get_url_by_id(1)[0][0]
    links, _ = db.get_tree(main_url)
    links = [(level, f, t) for level, f, t, _ in links]
    # print('\t[+] Getting unique URLS...')
    urls = get_unique_urls(links)
    if not len(urls):
        urls = [main_url]

    url_to_date = {}

    url_to_level = get_level(links, main_url)
    max_level = 4

    for url in urls:
        date = get_date(url, db)
        date = date.to_pydatetime()
        date = date.replace(tzinfo=None)
        url_to_date[url] = date

    hist_features = get_time_hist(url_to_date, url_to_level, main_url, max_level)
    list_features = [item for sublist in hist_features.values() for item in sublist]
    number_of_urls_published_before_source = get_number_of_urls_published_before_source(url_to_date, main_url)
    list_features.append(number_of_urls_published_before_source)
    number_of_urls_in_level = get_total_number_of_urls_in_level(url_to_level, max_level)
    list_features.extend(number_of_urls_in_level)
    return list_features


def get_fv(db_path):
    graph = get_graph(db_path, domain=True)
    sna_fv = get_graph_sna_feature_vector(graph)
    return sna_fv
    try:
        time_fv = get_time_vector(db_path)
    except Exception:
        print('fv_failed')
        return None
    sna_fv.extend(time_fv)
    return np.asarray(sna_fv)


def get_dataset(domain, normal_databases, propaganda_databases, graph_fv=False):
    dataset = []
    for db in propaganda_databases:
        g = get_graph(db, domain)
        if g is None:
            continue
        if graph_fv:
            fv = get_fv(db)
            dataset.append((fv, 1))
        else:
            dgl_graph = dgl.from_networkx(g, node_attrs=["degree_centrality", "node_fv", "one"])
            label = 1
            dataset.append((dgl_graph, label))
    ctr = len(dataset)

    for db in normal_databases:
        g = get_graph(db, domain)
        if g is None:
            continue
        if graph_fv:
            fv = get_fv(db)
            dataset.append((fv, 0))
        else:
            dgl_graph = dgl.from_networkx(g, node_attrs=["degree_centrality", "node_fv", "one"])
            dgl_graph = dgl.add_self_loop(dgl_graph)
            label = 0
            dataset.append((dgl_graph, label))
    return dataset


def get_nx_dataset(domain, normal_databases, propaganda_databases):
    dataset = []
    for db in normal_databases:
        g = get_graph(db, domain)
        if g is None:
            continue
        label = 0
        dataset.append((g, label))

    for db in propaganda_databases:
        g = get_graph(db, domain)
        if g is None:
            continue
        label = 1
        dataset.append((g, label))
    train_set, test_set = train_test_split(dataset, test_size=0.2, stratify=[l for _, l in dataset])
    train_set, val_set = train_test_split(train_set, test_size=0.2, stratify=[l for _, l in train_set])
    return train_set, val_set, test_set


if __name__ == '__main__':
    # you need to set paths to the databases, this is my stored at my local laptop

    normal_path = "C:\\EuVsDisinfo_dataset\\normal\\databases"
    normal_databases = [normal_path + "\\" + f for f in listdir(normal_path) if
                        isfile(join(normal_path, f)) and f.endswith(".db")]

    propaganda_path = "C:\\EuVsDisinfo_dataset\\propaganda\\databases"
    propaganda_databases = [propaganda_path + "\\" + f for f in listdir(propaganda_path) if
                            isfile(join(propaganda_path, f)) and f.endswith(".db")][:-1]

    # generate different dataset based on commenting code


    # this dataset contains graphs
    # entries are (dgl.graph, class), graph nodes has features g.nfeat['node_fv'] of dim 4 as starting feature vector
    # domain = True
    # pickle_name = 'domain_dataset.pickle' if domain else 'url_dataset.pickle'
    #
    # dataset = get_dataset(domain, normal_databases, propaganda_databases)
    # with open(pickle_name, 'wb') as f:
    #     pickle.dump(dataset, f)
    #
    # # this is dataset containing single vector for representation of entire graph
    # # entries are in form (np.array(), class)
    # pickle_name = 'graph_fv_dataset.pickle'
    #
    # dataset = get_dataset(True, normal_databases, propaganda_databases, graph_fv=True)
    # with open(pickle_name, 'wb') as f:
    #     pickle.dump(dataset, f)
    #
    # pickle_name = 'nx_domain_dataset.pickle'
    #
    # dataset = get_nx_dataset(True, normal_databases, propaganda_databases)
    # with open(pickle_name, 'wb') as f:
    #     pickle.dump(dataset, f)

    pickle_name = 'nx_dataset.pickle'

    dataset = get_nx_dataset(False, normal_databases, propaganda_databases)
    with open(pickle_name, 'wb') as f:
        pickle.dump(dataset, f)
