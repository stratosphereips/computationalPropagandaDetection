from datetime import datetime
import torch
import networkx as nx
import numpy as np
from itertools import product


def parse_date(text):
    d = None
    try:
        d = datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S")
    except Exception:
        pass
    try:
        if d is None:
            d = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass
    return d


def add_time_difference(dataset):
    for j in range(len(dataset)):
        g = dataset[j]
        g.nodes[0]["time_diff"] = 0
        g.nodes[0]["no_time"] = 0
        for e in g.edges:
            date_e0 = parse_date(g.nodes[e[0]]['publication_date'])
            date_e1 = parse_date(g.nodes[e[1]]['publication_date'])
            if date_e0 is not None and date_e1 is not None:
                g.nodes[e[0]]["time_diff"] = (date_e0 - date_e1).days
                g.nodes[e[0]]["no_time"] = 0
            else:
                g.nodes[e[0]]["time_diff"] = 0
                g.nodes[e[0]]["no_time"] = 1

    return dataset


def add_domain(dataset):
    for j in range(len(dataset)):
        g = dataset[j]
        node_domains = dict()
        for i in g.nodes():
            if g.nodes[i]['domain'] not in node_domains:
                node_domains[g.nodes[i]['domain']] = [i]
            else:
                node_domains[g.nodes[i]['domain']].append(i)

        for domain in node_domains:
            if len(node_domains[domain]) > 1:
                for d1, d2 in product(node_domains[domain], node_domains[domain]):
                    if d1 == d2:
                        continue
                    if d1 < d2:
                        g.add_edge(d1, d2, domain=1, link_type='domain')
                        g.add_edge(d2, d1, domain=1, link_type='domain')
    return dataset


def add_backward_edges(dataset):
    for j in range(len(dataset)):
        g = dataset[j][0]
        for e in g.edges:
            if g.edges[e]['link_type'] == 'title':
                g.add_edge(e[1], e[0], reversed_title=1, link_type='reversed_title')
            if g.edges[e]['link_type'] == 'link':
                g.add_edge(e[1], e[0], reversed_link=1, link_type='reversed_link')
    return dataset


def add_sna(dataset):
    for j in range(len(dataset)):
        g = dataset[j]
        unoriented_graph = nx.Graph(g)
        simple_graph = nx.DiGraph(g)
        reversesed_graph = simple_graph.reverse(copy=True)

        in_degree = nx.algorithms.in_degree_centrality(g)
        out_degree = nx.algorithms.out_degree_centrality(g)
        closeness = nx.algorithms.closeness_centrality(unoriented_graph)
        clustering = nx.algorithms.clustering(unoriented_graph)
        eig = nx.algorithms.eigenvector_centrality(reversesed_graph, max_iter=10000)

        for i in range(len(g.nodes)):
            feats = np.asarray([in_degree[i], out_degree[i], closeness[i], eig[i], clustering[i]])
            g.nodes[i]['sna'] = torch.tensor(feats)

    return dataset


def edges_to_id(dataset, e2id):
    for j in range(len(dataset)):
        g = dataset[j][0]
        for e in g.edges:
            if g.edges[e]['link_type'] == 'title':
                g.edges[e]['type'] = e2id['title']

            if g.edges[e]['link_type'] == 'reversed_title':
                g.edges[e]['type'] = e2id['reversed_title']

            if g.edges[e]['link_type'] == 'link':
                g.edges[e]['type'] = e2id['link']

            if g.edges[e]['link_type'] == 'reversed_link':
                g.edges[e]['type'] = e2id['reversed_link']

            if g.edges[e]['link_type'] == 'domain':
                g.edges[e]['type'] = e2id['domain']
    return dataset


def sna_node_embedding(dataset):
    for j in range(len(dataset)):
        g = dataset[j][0]
        for i in range(len(g.nodes)):
            n = g.nodes[i]
            g.nodes[i]['h'] = torch.tensor([
                *n['sna']
            ])
    return dataset


def all_node_embedding(dataset):
    is_list = True
    if type(dataset) is not list:
        is_list = False
        dataset = [dataset]
    for j in range(len(dataset)):
        g = dataset[j]
        for i in range(len(g.nodes)):
            n = g.nodes[i]
            g.nodes[i]['h'] = torch.tensor([
                0., 0., 0.,  # one hot level encoding
                n['time_diff'], n['no_time'],
                *n['sna']
            ])
            g.nodes[i]['h'][n['level']] = 1.
    if is_list:
        return dataset
    else:
        return dataset[0]

def all_but_sna_node_embedding(dataset):
    for j in range(len(dataset)):
        g = dataset[j][0]
        for i in range(len(g.nodes)):
            n = g.nodes[i]
            g.nodes[i]['h'] = torch.tensor([
                0., 0., 0.,  # one hot level encoding
                n['time_diff'], n['no_time'],
            ])
            g.nodes[i]['h'][n['level']] = 1.
    return dataset



