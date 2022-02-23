#!/usr/bin/env python3
import pandas as pd
import numpy as np
import argparse
from DB.propaganda_db import DB
from typing import Dict, List
from datetime import datetime
import pytz
import json


def flatten(list_of_lists):
    return [el for a_list in list_of_lists for el in a_list]


def get_number_of_urls_published_before_source(url_to_date: Dict[str, datetime], main_url: str) -> int:
    """
    Get count how many urls were published before the source date
    :param url_to_date: dictionary, where key is url, and value is date
    :param main_url: source urls
    :return: int
    """
    main_url_date = url_to_date[main_url]
    number_of_urls_published_before_source = 0
    for url, date in url_to_date.items():
        if date is None or main_url_date is None:
            continue
        if date < main_url_date:
            number_of_urls_published_before_source += 1
    return number_of_urls_published_before_source


def get_total_number_of_urls_in_level(url_to_level: Dict[str, int], max_level) -> List[int]:
    """
    Total Number of urls in each level.
    :param url_to_level: dictionary, where key is url, and value is level
    :param max_level: number of levels to consider
    :return: list of size max_level
    """
    total_number_of_urls_in_level = [0] * max_level
    for _, level in url_to_level.items():
        if level >= 0:  # main_url has level = -1
            total_number_of_urls_in_level[level] += 1
    return total_number_of_urls_in_level


def get_time_hist(url_to_date: Dict[str, datetime], url_to_level: Dict[str, int], main_url: str, max_level: int) -> Dict:
    # we calculate time histogram for each level
    # by this we are saving as time information so connection
    # print(url_to_date, main_url)
    main_url_date = url_to_date[main_url]

    minutes_hist_per_level = np.zeros((max_level, 24 * 60 * 2)).astype(int)  # 24h,60m, and 2 days
    hours_hist_per_level = np.zeros((max_level, 24 * 5)).astype(int)  # 24h and 5 days
    days_hist_per_level = np.zeros((max_level, 23)).astype(int)  # 23 days
    more_than_30_days_per_level = np.zeros(max_level)

    for url, date in url_to_date.items():
        if url == main_url:
            continue
        if date is None or main_url_date is None:
            # TODO: not sure what to do if the date is None
            continue
        # if date.tz is not None or main_url_date.tz is not None:
        #
        #     date.tz_localize(pytz.FixedOffset(180))
        #     main_url_date.tz_localize(pytz.FixedOffset(180))
        # print(date, main_url_date, date.tz, main_url_date.tz)
        day = (date - main_url_date).days
        if day < 0:
            continue
        if day < 2:  # for the first two days we are creating histogram for seconds
            minutes = int(((date - main_url_date).seconds) / 60)  # how many seconds from the main publication time
            level_url = url_to_level[url]  # calculating the level, level>1
            index = 24 * day * 60 + minutes  # calculating index: if day is zero, we will take first 1400 minutes
            d = minutes_hist_per_level[level_url]
            d[index] += 1
        elif day < 7:  # from day 2 to day 7 we calculate hours histogram
            hour = int(((date - main_url_date).seconds) / 3600)  # how many hours from the main publication time
            level_url = url_to_level[url]
            index = 24 * (day - 2) + hour
            hours_hist_per_level[level_url][index] += 1
        elif day <= 30:  # from day 7 to day 30 we calculate daily histogram
            level_url = url_to_level[url]
            index = day - 7
            days_hist_per_level[level_url][index] += 1
        else:  #
            level_url = url_to_level[url]
            more_than_30_days_per_level[level_url] += 1

    minutes_hist = minutes_hist_per_level.flatten().tolist()
    hour_hist = hours_hist_per_level.flatten().tolist()
    day_hist = days_hist_per_level.flatten().tolist()
    data = {"minute_hist": minutes_hist, "hour_hist": hour_hist, "day_hist": day_hist, "more_than_30_days": more_than_30_days_per_level.tolist()}
    return data


def get_level(links: List[tuple], main_url: str) -> Dict[str, int]:
    url_to_level = {}
    url_to_level[main_url] = -1  # index of the main url
    for (_, l1, l2) in links:
        if l2 not in url_to_level:
            url_to_level[l2] = url_to_level[l1] + 1  # others start with 0
    return url_to_level


def get_unique_urls(links: List[tuple]) -> List[str]:
    urls = set()
    for (_, l1, l2) in links:
        urls.add(l2)
        urls.add(l1)
    return list(urls)


def get_date(url, db):
    return pd.to_datetime(db.get_date_published_url(url))

def store_features_in_file(features):
    """
    Store the features in a file
    """
    # Open CSV file of features
    f = open(args.csv_output_file, 'a+')
    features = json.dumps(features)
    f.write(features)
    f.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to build features from graph", type=str, required=True)
    parser.add_argument("-d", "--database_path", help="Path to the database", type=str, required=True)
    parser.add_argument("-w", "--csv_output_file", help="CSV output file", type=str, required=False, default='propaganda-graph-features.csv')
    args = parser.parse_args()
    
    db = DB(args.database_path)
    print(f'Generating the features for all the links in the DB {args.database_path}')
    print('\t[+] Getting all the links...')


    main_url = args.link
    print('\t[+] Getting the tree...')
    links, _ = db.get_tree(main_url)
    links = [(level, f, t) for level, f, t, _ in links]
    print('\t[+] Getting unique URLS...')
    urls = get_unique_urls(links)

    url_to_date = {}

    url_to_level = get_level(links, main_url)
    max_level = 4

    for url in urls:
        print(f'\t[+] Processing URL {url}')
        date = get_date(url, db)
        print(f'\t\t - Date: {date}')
        url_to_date[url] = date

    print('\t[+] Getting the time features')
    hist_features = get_time_hist(url_to_date, url_to_level, main_url, max_level)
    print('\t[+] Storing features in file')
    store_features_in_file(hist_features)
    number_of_urls_published_before_source = get_number_of_urls_published_before_source(url_to_date, main_url)
    print(f'\t[+] Number of urls published before source: {number_of_urls_published_before_source}')
    number_of_urls_in_level = get_total_number_of_urls_in_level(url_to_level, max_level)
    print(f'\t[+] Number of urls in level: {number_of_urls_in_level}')
