import networkx as nx
import numpy as np
from DB.propaganda_db import DB
from create_features import *
from os import listdir
from os.path import isfile, join
import pickle

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
    print(db_path)
    db = DB(db_path)
    urls = db.get_url_by_id(1)[0][0]
    cur_edges, cur_nodes = db.get_tree(urls)

    new_nodes = set(cur_nodes.keys())
    new_edges = [((source, target), {'edge_type': edge_type}) for _, source, target, edge_type
                 in cur_edges]
    if len(new_edges) <= 1:
        return None

    if domain:
        new_nodes = {filter_name(n) for n in new_nodes}

    G = nx.DiGraph(label="prop")
    G.add_nodes_from(new_nodes)
    for e in new_edges:
        f, t = e[0]
        if domain:
            f = filter_name(f)
            t = filter_name(t)
        G.add_edge(f, t, **e[1])

    reversed_G = G.reverse(copy=True)

    degree = nx.algorithms.degree_centrality(G)
    betweenness = nx.algorithms.betweenness_centrality(G)

    eig = nx.algorithms.eigenvector_centrality(reversed_G, max_iter=10000)

    degree_centrality = nx.algorithms.degree_centrality(G)
    clustering = nx.algorithms.clustering(G)
    nx.algorithms.transitivity(G)

    for n in G.nodes:
        print(n)
        G.nodes[n]["degree_centrality"] = np.asarray([degree_centrality[n]], dtype=np.float32)
        G.nodes[n]["node_fv"] = np.asarray([degree[n], betweenness[n], eig[n], clustering[n]], dtype=np.float32)
        print(G.nodes[n]["node_fv"])
        G.nodes[n]["one"] = np.ones(1, dtype=np.float32)

    return G


def get_graph_sna_feature_vector(graph):
    if graph is None:
        return np.zeros(9)
    degree = nx.algorithms.degree_centrality(graph)
    betweenness = nx.algorithms.betweenness_centrality(graph)

    closeness = nx.algorithms.closeness_centrality(graph)
    eig = nx.algorithms.eigenvector_centrality(graph, max_iter=10000)

    # clustering
    triangles = nx.algorithms.triangles(graph)
    clustering = nx.algorithms.clustering(graph)
    radius = nx.algorithms.distance_measures.radius(graph)

    transitivity = nx.algorithms.transitivity(graph)

    edge_types = [n[-1]["edge_type"] for n in graph.edges(data=True)]

    link_num = edge_types.count("link")
    features = np.asarray([sum(closeness.values()) / len(degree), sum(degree.values()) / len(degree),
                           sum(betweenness.values()) / len(degree), sum(eig.values()) / len(degree),
                           sum(triangles.values()) / len(degree), sum(clustering.values()) / len(degree),
                           transitivity, radius, link_num / max(1, len(edge_types))])

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
        # print(f'\t[+] Processing URL {url}')
        date = get_date(url, db)
        date = date.to_pydatetime()
        date = date.replace(tzinfo=None)
        # print(f'\t\t - Date: {date}')
        url_to_date[url] = date

    # print('\t[+] Getting the time features')
    hist_features = get_time_hist(url_to_date, url_to_level, main_url, max_level)
    list_features = [item for sublist in hist_features.values() for item in sublist]
    # print(hist_features)
    # print('\t[+] Storing features in file')
    # store_features_in_file(hist_features)
    number_of_urls_published_before_source = get_number_of_urls_published_before_source(url_to_date, main_url)
    list_features.append(number_of_urls_published_before_source)
    # print(number_of_urls_published_before_source)
    # print(f'\t[+] Number of urls published before source: {number_of_urls_published_before_source}')
    number_of_urls_in_level = get_total_number_of_urls_in_level(url_to_level, max_level)
    list_features.extend(number_of_urls_in_level)
    # print(number_of_urls_in_level)
    # print(f'\t[+] Number of urls in level: {number_of_urls_in_level}')
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


def get_dataset(domain, normal_databases, propaganda_databases):
    # print(propaganda_databases)
    dataset = []
    for db in propaganda_databases:
        g = get_graph(db, domain)
        if g is None:
            continue
        dgl_graph = dgl.from_networkx(g, node_attrs=["degree_centrality", "node_fv", "one"])
        dgl_graph = dgl.add_self_loop(dgl_graph)
        label = 1
        dataset.append((dgl_graph, label))
    ctr = len(dataset)
    print("propaganda: ", ctr)

    for db in normal_databases:
        g = get_graph(db, domain)
        if g is None:
            continue
        dgl_graph = dgl.from_networkx(g, node_attrs=["degree_centrality", "node_fv", "one"])
        dgl_graph = dgl.add_self_loop(dgl_graph)
        label = 0
        dataset.append((dgl_graph, label))
    print("nodmal: ", len(dataset) - ctr)
    return dataset


if __name__ == '__main__':
    normal_path = "C:\\EuVsDisinfo_dataset\\normal\\databases"
    normal_databases = [normal_path + "\\" + f for f in listdir(normal_path) if
                        isfile(join(normal_path, f)) and f.endswith(".db")]

    propaganda_path = "C:\\EuVsDisinfo_dataset\\propaganda\\databases"
    propaganda_databases = [propaganda_path + "\\" + f for f in listdir(propaganda_path) if
                            isfile(join(propaganda_path, f)) and f.endswith(".db")][:-1]

    domain = True

    pickle_name = 'domain_dataset.pickle' if domain else 'url_dataset.pickle'

    dataset = get_dataset(domain, normal_databases, propaganda_databases)
    with open(pickle_name, 'wb') as f:
        pickle.dump(dataset, f)
