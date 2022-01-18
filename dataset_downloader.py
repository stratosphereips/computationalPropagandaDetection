import importlib
import argparse
import os
import sys

import graph

wnm = importlib.import_module("web-network-mapper")


def main(data, idx_from):
    for idx in range(idx_from, len(data)):
        data_root = '/data/propagandadetection/EuVsDisinfo_dataset/'

        sys.stdout = open(f'{data_root}logs/{idx}.log', 'w')
        link = data[idx]
        with open(f'{data_root}logs/dataset_downloader.log', 'a') as log_file:
            try:
                db_path = f'{data_root}databases/propaganda{idx}.db'
                wnm.main(link, is_propaganda=True, database=db_path, number_of_levels=2, urls_threshold=0.1)
                log_file.write(f'{idx} OK\n')
            except KeyboardInterrupt:
                break
            except Exception as e:
                log_file.write(f'{idx} FAIL {e}\n')
            domain_graph_name = data_root + f'graphs/domain_{idx}.html'
            graph.create_domain_centered(link, db_path, graph_name=domain_graph_name)
            timeline_graph_name = data_root + f'graphs/timeline_{idx}.html'
            graph.create_date_centered(link, db_path, graph_name=timeline_graph_name)
        sys.stdout.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--from_idx", help="Start downloading from index ", type=int, required=False, default=90
    )
    parser.add_argument(
        "-u", "--url_file", help="txt file containing urls", type=str, required=False, default="propaganda_data.txt"
    )
    args = parser.parse_args()
    with open(args.url_file) as file:
        all_links = file.read().splitlines()
        print(len(all_links))
    main(all_links, args.from_idx)
