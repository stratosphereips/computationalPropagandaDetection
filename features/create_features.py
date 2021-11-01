#!/usr/bin/env python3
import pandas as pd
import numpy as np
import argparse
from typing import Dict, List
from datetime import datetime
import sys
import os

sys.path.append(os.getcwd())
from DB.propaganda_db import DB


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
        if date != None and main_url_date != None:
            if date < main_url_date:
                number_of_urls_published_before_source += 1
        else:
            continue
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


def get_time_hist(url_to_date: Dict[str, datetime], url_to_level: Dict[str, int], main_url: str,
                  max_level: int) -> Dict:
    """
    Generate the features based on time
    - For each level:
        - Calculate a histogram of how many links there are by:
            - In the next 48hs after the publication date of the main URL (2 days). 
                - Compute the histogram of urls published by minute
            - After more than 48hs of the publication, for the next 120hs (5 days), that is from > 2nd day to <= 7th day.
                - Compute the histogram of urls published by hour
            - After more than 168hs of the publication, for the next 23 days, that is from > 7th day to <= 30th
                - Compute the histogram of urls published by day

              Publication of    Up to                        More than 48hs
              main URL          48hs hs                      and up to 120hs
                    | By minute |         By hour             |                    By day
                    \/          \/                            \/
            Days: |--*--|-----|--*--|-----|-----|-----|-----|--*--|-----|-----|-----|-----|-----|-----|-----|-----|-----|
                     1     2     3     4     5     6     7     8     9    10    11    12    13    14    15    16   17...
    """
    # by this we are saving as time information so connection
    main_url_date = url_to_date[main_url]

    # Create empty lists of 0 for each type of histogram
    minutes_hist_per_level = np.zeros((max_level, 24 * 60 * 2)).astype(int)  # 24h,60m, and 2 days
    hours_hist_per_level = np.zeros((max_level, 24 * 5)).astype(int)  # 24h and 5 days
    days_hist_per_level = np.zeros((max_level, 23)).astype(int)  # 23 days
    more_than_30_days_per_level = np.zeros(max_level).astype(int)  # one per each level
    past_in_time_in_days_per_level = np.zeros((max_level, 8)).astype(int)

    for url, date in url_to_date.items():
        if args.debug > 0:
            print(f'Processing features for URL {url}, on date {date}')
        # Avoid processing twice the main url
        if url == main_url:
            continue
        if date is None:
            # TODO: not sure what to do if the date is None
            continue
        if date != None and main_url_date != None:

            # TODO: Convert this to hours instead of days
            hours = (date - main_url_date).seconds / (60 * 60)
            days = hours / 24  # days is float, so it is actually day + part of the hours 2.1 = 2 days and
            if args.debug > 0:
                print(
                    f'\tMain URL date: {main_url_date}, type {type(date)}. Other URL date {date}, type {type(date)}. Difference in days: {day}')
            if 0 <= hours < 48:  # for the first two days we are creating histogram for seconds
                minutes = int((date - main_url_date).seconds / 60)  # how many minutes from the main publication time
                level_url = url_to_level[url]  # calculating the level, level>1
                index = minutes  # calculating index: if day is zero, we will take first 2779 minutes
                if args.debug > 0:
                    print(
                        f'\t\tBetween 0 and 2 days. The minutes is {minutes} the level is {level_url} and the index is {index}')
                d = minutes_hist_per_level[level_url]
                d[index] += 1
            elif 2 <= days < 7:  # from day 2 to day 7 we calculate hours histogram
                level_url = url_to_level[url]
                index = int(hours - 24 * 2)  # ignoring the firs two days, from 0 to 119 index
                if args.debug > 0:
                    print(
                        f'\t\tBetween 3 and 7 days. The hours is {hour} the level is {level_url} and the index is {index}')
                hours_hist_per_level[level_url][index] += 1
            elif 7 <= days < 30:  # from day 7 to day 30 we calculate daily histogram
                level_url = url_to_level[url]
                index = days - 7  # from 0 to 23
                if args.debug > 0:
                    print(f'\t\tBetween 7 and 30 days. The level is {level_url} and the index is {index}')
                days_hist_per_level[level_url][index] += 1
            elif days >= 30:  # from day 7 to day 30 we calculate daily histogram
                level_url = url_to_level[url]
                more_than_30_days_per_level[level_url] += 1
            elif days < 0:  # It was published before the main url
                positive_days = abs(days)  # store the first 7 days per days
                if positive_days < 7:
                    index = positive_days  # index is starting from 0 to 6
                else:
                    index = 7  # less than 7 days in the past got grouped together
                level_url = url_to_level[url]
                past_in_time_in_days_per_level[level_url][index] += 1
                if args.debug > 0:
                    print(f'\t\t[Error] URL was published in {date}, before the main url on {main_url_date}.')
                pass

    minutes_hist = minutes_hist_per_level.flatten().tolist()
    hour_hist = hours_hist_per_level.flatten().tolist()
    day_hist = days_hist_per_level.flatten().tolist()
    past_in_time_in_days = past_in_time_in_days_per_level.flatten().tolist()

    data = {"minute_hist": minutes_hist,
            "hour_hist": hour_hist,
            "day_hist": day_hist,
            "more_than_30_days": more_than_30_days_per_level.tolist(),
            "less_than_date_published": past_in_time_in_days
            }
    return data


def get_level(links: List[tuple], main_url: str) -> Dict[str, int]:
    """
    Finds in which level is each URL

    Input: List of links
    Output: Dict of URLs with levels
    """
    url_to_level = {}
    url_to_level[main_url] = -1  # index of the main url
    # print(links)
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


def get_date(url):
    return pd.to_datetime(db.get_date_published_url(url))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to build features from graph", type=str, required=True)
    parser.add_argument("-d", "--database_path", help="Path to the database", type=str, required=True)
    parser.add_argument("-e", "--debug", help="Debug", type=int, required=False, default=0)
    parser.add_argument("-v", "--verbosity", help="Verbosity", type=int, required=False, default=0)
    args = parser.parse_args()
    print(f'Using DB {args.database_path} and link {args.link}')

    # Open the DB, get the main_url, links and other URLs
    db = DB(args.database_path)
    main_url = args.link
    links = db.get_tree(main_url)
    urls = get_unique_urls(links)

    url_to_date = {}

    url_to_level = get_level(links, main_url)
    max_level = 2

    for url in urls:
        date = get_date(url)
        # Be sure the dates have a timezone or not, but we can not mix!
        if date is not None:
            date = date.tz_localize(None)
        url_to_date[url] = date
        # if args.debug > 0:
        # print(f'\tURL: {url}, date: {date}')

    # Generate the features that are a histogram of time
    hist_features = get_time_hist(url_to_date, url_to_level, main_url, max_level)
    if args.verbosity > 0:
        print(hist_features)

    # Get the number of urls published before the source
    number_of_urls_published_before_source = get_number_of_urls_published_before_source(url_to_date, main_url)
    print("Number of urls published before source", number_of_urls_published_before_source)

    # Get the total number of urls in each level 
    number_of_urls_in_level = get_total_number_of_urls_in_level(url_to_level, max_level)
    print("Number of urls in level", number_of_urls_in_level)
