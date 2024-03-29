#!/usr/bin/env python
import os
import argparse
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from DB.propaganda_db import DB
from serpapi_utils import get_hash_for_url
from pyvis.network import Network
from datetime import datetime, date, timedelta

TIMELINE_WIDTH = 8  # scale of the x-axis of the timeline


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


def create_date_centered(url, db_path, time_window=2, id=0, graph_name=None):
    db = DB(db_path)
    edges, nodes = db.get_tree(url)

    # find what dates are used and erase duplicates and None
    original_date = None
    if nodes[url][0]:
        original_date = datetime.strptime(nodes[url][0][:10], '%Y-%m-%d').date()

    first_date = date.today() - timedelta(days=time_window * 365)

    date_of_query_str = db.get_date_of_query_url(url).split(' ')[0]  # we are interested only in date not exact time
    date_of_query = datetime.strptime(date_of_query_str, '%Y-%m-%d').date()

    dates = [str(nodes[url][0][:10]) if nodes[url][0] is not None else None for url in nodes]
    dates.append(None)
    dates_set = {str(d) for d in dates}
    dates_set.add(str(date_of_query))
    unique_dates = sorted(list(dates_set))[:-1]
    pos = {d: TIMELINE_WIDTH * (datetime.strptime(d, '%Y-%m-%d').date() - first_date).days for d in unique_dates}
    pos["Old article"] = 0

    g = Network('700px', '1500', notebook=False, directed=False)

    # creating the timeline
    for i, n in enumerate(unique_dates):
        if original_date is None or n != original_date and n is not None:
            cur_date = datetime.strptime(n, '%Y-%m-%d').date()
            if cur_date == original_date:  # original query date to be red
                g.add_node(str(original_date), label=' ', title='original date' + str(original_date), color="red",
                           x=pos[str(cur_date)], y=0, physics=True, shape='diamond', size=25,
                           fixed={'x': True, 'y': True})
            elif cur_date == date_of_query:  # mark today on the timeline green
                g.add_node(n, label=' ', title=n, color="green", x=pos[str(cur_date)], y=0,
                           physics=False, shape='diamond', size=25, fixed={'x': True, 'y': True})
            elif first_date < cur_date < date_of_query:  # the main timeline
                g.add_node(n, label=' ', title=n, color="#cccccc", x=pos[str(cur_date)], y=0, physics=False,
                           shape='diamond', size=20, fixed={'x': True, 'y': True})
            elif cur_date >= date_of_query:  # different version for future dates
                g.add_node(n, label=' ', title=n, color="#555555", x=pos[str(cur_date)], y=0, physics=False,
                           shape='diamond', size=15, fixed={'x': True, 'y': True})
            elif cur_date <= first_date:  # add node to gather all articles older than time_window years
                g.add_node("Old article", label=' ', title="Old article", color='yellow', x=0, y=0, physics=False,
                           shape='diamond', size=35, fixed={'x': True, 'y': True})

    centers = {source for lvl, source, _, link_type in edges if lvl == 2}
    node_color = {}
    for n in nodes:
        link_type = [link_type for lvl, source, target, link_type in edges if target == n]
        if link_type:
            node_color[n] = "green" if link_type[0] == "link" else "red"
        else:
            node_color[n] = "red"
    clusters = {}
    for c in centers:
        clusters[c] = [(target, link_type) for _, source, target, link_type in edges if source == c]

    side_wrt_timeline = 1
    for c in clusters:
        side_wrt_timeline *= -1
        if nodes[c][0] is not None:
            cur_date = datetime.strptime(nodes[c][0][:10], '%Y-%m-%d').date()
            target = nodes[c][0][:10]
            if cur_date <= first_date:
                target = "Old article"
        else:
            cur_date = None
        by_link, by_title = node_color[c] == "red", node_color[c] == "green"
        s = 1
        for l2, link_type in clusters[c]:
            if nodes[l2][0] is not None and nodes[c][0] is not None and nodes[l2][0][:10] == nodes[c][0][:10]:
                s += 1
                if link_type == "link":
                    by_link = True
                if link_type == "title":
                    by_title = True
        if by_title and by_link:
            color = "purple"
        elif by_title:
            color = "green"
        elif by_link:
            color = "red"

        g.add_node(c, label=filter_name(c), title=str(len(clusters[c])), size=30, mass=2,
                   length=30 * len(clusters[c]), color=node_color[c],
                   y=side_wrt_timeline * 30 * len(clusters[c]),
                   fixed={'x': False, 'y': True})
        if cur_date is not None:
            g.add_edge(c, target, color=color, width=s, length=1, title=str(s), label=str(s), dashes=[8 * s, 8 * s])

        # width and color of edges
        for link, link_type in clusters[c]:
            if nodes[link][0] is not None:
                s = 0
                cur_date = datetime.strptime(nodes[link][0][:10], '%Y-%m-%d').date()
                by_link, by_title = False, False
                for l2, s_type in clusters[c]:
                    if nodes[l2][0] is not None and nodes[l2][0][:10] == nodes[link][0][:10]:
                        s += 1
                        if s_type == "link":
                            by_link = True
                        if s_type == "title":
                            by_title = True
                if by_title and by_link:
                    color = "purple"
                elif by_title:
                    color = "green"
                elif by_link:
                    color = "red"

                target = nodes[link][0][:10]
                if cur_date <= first_date:
                    target = "Old article"
                g.add_edge(c, target, title=str(s), label=str(s), physics=False, width=s, color=color)

    # adding the rest of level 1 nodes that are not referenced by an level 2
    side_wrt_timeline = 1
    for n in nodes:
        if nodes[n][0] is not None:
            cur_date = datetime.strptime(nodes[n][0][:10], '%Y-%m-%d').date()
            target = nodes[n][0][:10]
            if cur_date <= first_date:
                target = "Old article"
            g.add_node(n, size=10, label=' ', title=n, y=side_wrt_timeline * 30, x=pos[target], color=node_color[n],
                       fixed={'x': True, 'y': True}, physics=False)
            g.add_edge(n, target, physics=False, hidden=True)
        side_wrt_timeline *= -1

    g.show_buttons()
    # g.set_edge_smooth('smooth')
    if graph_name is None:
        if not os.path.exists("graphs"):
            os.makedirs("graphs")
        graph_name = os.path.join("graphs", f"{get_hash_for_url(url)}_TIMELINE_CENTERED_GRAPH.html")
        if id:
            graph_name = os.path.join("graphs",
                                      f"{id}_{'Propaganda' if id <= 20 else 'Not_propaganda'}_TIMELINE_CENTERED_GRAPH.html")
    g.save_graph(graph_name)
    # g.save_graph(os.path.join("graphs", f"{get_hash_for_url(url)}_TIMELINE_CENTERED_GRAPH.html"))
    # g.show(f'level_timeline.html')


def create_domain_centered(urls, db_path, id=0, graph_name=None):
    db = DB(db_path)
    edges = list()
    centers = dict()

    cur_edges, cur_nodes = db.get_tree(urls)
    cur_centers = {
        filter_name(url): (cur_nodes[url][1], [n for n in cur_nodes.keys() if filter_name(n) == filter_name(url)]) for
        url in list(cur_nodes.keys())[::-1]}
    for e in cur_edges:
        edges.append(e)
    centers = {**centers, **cur_centers}

    from_to_edges = dict()
    for _, source, target, _ in edges:
        filtered_source, filtered_target = filter_name(source), filter_name(target)
        if filtered_source not in from_to_edges:
            from_to_edges[filtered_source] = []
        from_to_edges[filtered_source].append(filtered_target)

    colors = ["red", "blue", "green"]
    # colors = ["#9060690", "#9060690", "#9060690"]

    g = Network('700px', '1500px')

    for n in centers.keys():
        g.add_node(n, color=colors[centers[n][0]], title=str(len(centers[n][1])),
                   size=10 * np.log(len(centers[n][1]) + 3))
        for t in centers[n][1]:
            g.add_node(t, label=' ', title=t, hidden=True)
    #         g.add_edge(n,t, hidden=True)
    for _, source, target, _ in edges:
        filtered_source, filtered_target = filter_name(source), filter_name(target)
        from_count = len([t for t in from_to_edges[filtered_source] if t == filtered_target])
        to_count = 0
        if filtered_target in from_to_edges:
            to_count = len([t for t in from_to_edges[filtered_target] if t == filtered_source])
        g.add_edge(filter_name(source), filter_name(target), width=3 * np.log(to_count + from_count + 1),
                   title=from_count + to_count)
    g.show_buttons()
    if graph_name is None:
        if not os.path.exists("graphs"):
            os.makedirs("graphs")
        if id:
            graph_name = os.path.join("graphs",
                                      f"{id}_{'Propaganda' if id <= 20 else 'Not_propaganda'}_DOMAIN_CENTERED_GRAPH.html")
        else:
            graph_name = os.path.join("graphs", f"{get_hash_for_url(urls)}_DOMAIN_CENTERED_GRAPH.html")
    g.save_graph(graph_name)
    # g.show(f'web-centered-graph.html')


def build_a_graph(all_links, search_link, id=0):
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
    # nx.draw(G, labels=labels, node_color=colors)
    # nx.draw_random(G, node_color=colors)
    # nx.draw_shell(G, node_color=colors)
    # nx.draw_spectral(G, node_color=colors)
    # nx.draw_circular(G, node_color=colors)
    # nx.draw_networkx_labels(G, node_color=colors)
    # nx.draw_spectral(G)
    # pos = nx.spring_layout(G)
    # nx.draw_networkx_labels(G, pos, labels, font_size=16)
    # plt.show()
    if not os.path.exists("graphs"):
        os.makedirs("graphs")
    fig_name_hashed_link = get_hash_for_url(search_link)
    graph_name = os.path.join("graphs", fig_name_hashed_link)
    if id:
        graph_name = os.path.join("graphs", str(id))
    plt.savefig(graph_name)
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to check is distribution pattern", type=str, required=True)
    parser.add_argument("-d", "--path_to_db", help="Path to Database", type=str)

    args = parser.parse_args()

    print(args.path_to_db)
    db = DB(args.path_to_db)

    print(args.link)
    all_links, _ = db.get_tree(args.link)
    links_without_level = [(from_id, to_id) for (_, from_id, to_id, _) in all_links]
    build_a_graph(links_without_level, args.link)
    create_domain_centered(args.link, args.path_to_db)
    create_date_centered(args.link, args.path_to_db)
    # for i in range(1, 2):
    #     print(i)
    #     # try:
    #     link = DATA[i]
    #
    #     db_path = f"DB/v2/propaganda.{i}.db"
    #     db = DB(db_path)
    #     print("db loaded")
    #
    #     all_links, _ = db.get_tree(link)
    #     # links_without_level = [(from_id, to_id) for (_, from_id, to_id, _) in all_links]
    #     # build_a_graph(links_without_level, link, i)
    #
    #     create_domain_centered(link, db_path, i)
    #     create_date_centered(link, db_path, 2, i)
    #     # except Exception as e:
    #     #     print(f"{i} failed {e}")
