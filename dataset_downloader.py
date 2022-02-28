import importlib
import argparse
import os
import sys

import graph

wnm = importlib.import_module("web-network-mapper")


def main(data, idx_from, number_to_download, redirect, process_id, propaganda):
    for idx in range(idx_from, min(idx_from + number_to_download, len(data))):
        if propaganda:
            data_root = '/data/propagandadetection/EuVsDisinfo_dataset/propaganda/'
        else:
            data_root = '/data/propagandadetection/EuVsDisinfo_dataset/normal/'


        data_root = 'C:\\data\\'
        if redirect:
            sys.stdout = open(f'{data_root}logs/{idx}.log', 'w')
            sys.stderr = open(f'{data_root}logs/{idx}.err', 'w')
        link = data[idx]
        with open(f'{data_root}logs/dataset_downloader_{process_id}.log', 'a') as log_file:
            try:
                db_path = f'{data_root}databases/propaganda{idx}.db'
                wnm.main(link, is_propaganda=True, database=db_path, number_of_levels=2, urls_threshold=0.1, max_results=70)
                log_file.write(f'{idx} OK\n')
            except KeyboardInterrupt:
                return
            except Exception as e:
                log_file.write(f'{idx} FAIL {e}\n')
                continue
            domain_graph_name = data_root + f'graphs/domain_{idx}.html'
            graph.create_domain_centered(link, db_path, graph_name=domain_graph_name)
            timeline_graph_name = data_root + f'graphs/timeline_{idx}.html'
            graph.create_date_centered(link, db_path, graph_name=timeline_graph_name)
        if redirect:
            sys.stdout.close()
            sys.stderr.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f", "--from_idx", help="which index to download", type=int, required=False, default=0
    )
    parser.add_argument(
        "-u", "--url_file", help="txt file containing urls", type=str, required=False, default="propaganda_data.txt"
    )
    parser.add_argument(
        "-p", "--process_id", help="process id that is running (for logging purposes if running multiple scripts)",
        default=0, type=int
    )
    parser.add_argument(
        "-n", "--number_to_download", help="Number of urls to download, it will download dataset [from -f to -f+-n]",
        default=100, type=int
    )
    parser.add_argument("-r", "--redirect", help="redirect output to log file", action='store_true')
    parser.add_argument("-p", "--propaganda", help="is data file propaganda", action='store_true')
    args = parser.parse_args()
    with open(args.url_file) as file:
        all_links = file.read().splitlines()
        print(len(all_links))
    main(all_links, args.from_idx, args.number_to_download, args.redirect, args.process_id, args.propaganda)
