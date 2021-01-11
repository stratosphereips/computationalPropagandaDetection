#!/usr/bin/env python
import os
import networkx as nx
import argparse
from DB.propaganda_db import DB
import matplotlib.pyplot as plt
from serpapi_utils import get_hash_for_url


def filter_name(url):
    # Takes out 'www' from the domain name in the URL.
    # First finds the domain in the URL
    if "http" in url:
        # we are searching a domain
        basename = url.split("/")[2]
    else:
        # if a title, just the first word
        basename = url.split(" ")[0]
        pass
    # Takes out the 'www'
    if "www" == basename[:3]:
        return basename[4:]
    return basename


def build_a_graph(all_links, search_link):
    """
    Builds a graph based on the links between the urls.
    """

    # Labels for each node. In this case it is the basename domain of the URL
    labels = {}
    # Not sure what are the levels. Levels in the graph?
    levels = {search_link: 0}

    # Create graph
    G = nx.DiGraph()

    G.add_edges_from(all_links)

    # Manage colors. They are used for the levels of linkage
    colors = ["black"]
    possible_colors = ["red", "green", "c", "m", "y"]

    # For each link, add a label and a color
    for (from_link, to_link) in all_links:
        # Add labels to the node
        labels[from_link] = filter_name(from_link)
        labels[to_link] = filter_name(to_link)

        # Count the levels
        if to_link not in levels:
            # Add as level, the level of the parent + 1. So level is 0, 1, 2, etc.
            levels[to_link] = levels[from_link] + 1
            # Based on the levels, add a color
            colors.append(possible_colors[levels[to_link] % len(possible_colors)])
    # print(levels)
    # nx.draw(G, labels=labels, node_color=colors, with_labels=True)
    # nx.draw_spring(G, labels=labels, node_color=colors)
    # nx.draw_kamada_kawai(G, node_color=colors)
    nx.draw_planar(G, labels=labels, node_color=colors)
    # nx.draw_random(G, node_color=colors)
    # nx.draw_shell(G, node_color=colors)
    # nx.draw_spectral(G, node_color=colors)
    # nx.draw_circular(G, node_color=colors)
    # nx.draw_networkx_labels(G, node_color=colors)
    # nx.draw_spectral(G)
    # pos = nx.spring_layout(G)
    # nx.draw_networkx_labels(G, pos, labels, font_size=16)
    plt.show()
    if not os.path.exists("graphs"):
        os.makedirs("graphs")
    fig_name_hashed_link = get_hash_for_url(search_link)
    plt.savefig(os.path.join("graphs", fig_name_hashed_link))


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to check is distribution pattern", type=str)
    parser.add_argument("-d", "--path_to_db", default="DB/propaganda.db", help="Path to Database", type=str)

    args = parser.parse_args()

    db = DB(args.path_to_db)

    all_links = db.get_tree(args.link)
    links_without_level = [(from_id, to_id) for (_, from_id, to_id) in all_links]
    build_a_graph(links_without_level, args.link)
