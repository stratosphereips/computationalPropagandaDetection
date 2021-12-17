import importlib
import argparse
import os

wnm = importlib.import_module("web-network-mapper")


def main(data, idx_from):
    if not os.path.exists('logs'):
        os.makedirs('logs')
    for idx in range(idx_from, len(data)):
        link = data[idx]
        with open('logs/dataset_downloader_log.txt', 'a') as log_file:
            try:
                wnm.main(link, is_propaganda=True, database=f'DB/databases/propaganda_{idx}.db', number_of_levels=1)
                log_file.write(f'{idx} OK\n')
            except KeyboardInterrupt:
                break
            except Exception as e:
                log_file.write(f'{idx} FAIL {e}\n')


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
