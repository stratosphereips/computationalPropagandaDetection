#!/usr/bin/env python3
#
# Program to extract all the features from a DB
# 
import pandas as pd
import numpy as np
import argparse
from DB.propaganda_db import DB
from typing import Dict, List
from datetime import datetime


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
        if date is None:
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


def get_time_histogram(url_to_date: Dict[str, datetime], url_to_level: Dict[str, int], main_url: str, max_level: int) -> Dict:
    """
    We calculate time histogram for each level
    The histogram is ... 
    by this we are saving as time information so connection
    """
    main_url_date = url_to_date[main_url]

    # How many links happened on each minute, on each level
    minutes_hist_per_level = np.zeros((max_level, 24 * 60 * 2)).astype(int)  # 24h,60m, and 2 days
    # How many links happened on each hour, on each level
    hours_hist_per_level = np.zeros((max_level, 24 * 5)).astype(int)  # 24h and 5 days
    # How many links happened on each day, on each level
    days_hist_per_level = np.zeros((max_level, 23)).astype(int)  # 23 days
    # How many links happened after more than 30 days, on each level
    more_than_30_days_per_level = np.zeros(max_level)

    for url, date in url_to_date.items():
        if url == main_url:
            continue
        print(date, main_url_date)
        if date is None:
            # TODO: not sure what to do if the date is None
            continue
        # Consider here date OLDER than the mail url. Basically detection of fake dates
        day = (date - main_url_date).days
        print(f'day: {day}')
        if day < 0: 
            # Fake date detected. The date of the link is older than main url
            print(f'Warning. The date of the link is {date}, and OLDER the date of the main url is {main_url_date}.')
            return False
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
    """
    Creates a dict with URLs keys and their levelss

    Input: List of links
    Output: Dict of URLs with levels
    """
    url_to_level = {}
    for (level, l1, l2) in links:
        if l2 not in url_to_level:
            url_to_level[l2] = level 
    return url_to_level


def get_unique_urls(links: List[tuple]) -> List[str]:
    """
    Extract the 2 urls from each tuple (level, parent_url, child_url)
    """
    urls = set()
    for (_, l1, l2) in links:
        urls.add(l2)
        urls.add(l1)
    return list(urls)


def get_date(url):
    """
    Return the date of publication of the URL, from the DB, as datetime
    """
    return pd.to_datetime(db.get_date_published_url(url))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to build features from graph", type=str, required=True)
    parser.add_argument("-d", "--database_path", help="Path to the database", type=str, required=True)
    parser.add_argument("-m", "--max_level", help="Max level to analyze", type=int, required=False, default=4)
    args = parser.parse_args()
    print(f'Using DB {args.database_path} and link {args.link}')

    # Open the DB, get the main_url, links and other URLs
    db = DB(args.database_path)
    main_url = args.link
    # Get all the links from the main url. Links is a list of tuples, with (levels, parent_url, child_url)
    links = db.get_tree(main_url)
    # Extract all the URLs in all links
    urls = get_unique_urls(links)

    url_to_date = {}

    # Get a dictionary of urls and their levels
    url_to_level = get_level(links, main_url)

    # Get the date of each URL
    for url in urls:
        date = get_date(url)
        url_to_date[url] = date

    hist_features = get_time_histogram(url_to_date, url_to_level, main_url, args.max_level)
    number_of_urls_published_before_source = get_number_of_urls_published_before_source(url_to_date, main_url)
    print("Number of urls published before source", number_of_urls_published_before_source)
    number_of_urls_in_level = get_total_number_of_urls_in_level(url_to_level, args.max_level)
    print("Number of urls in level", number_of_urls_in_level)
