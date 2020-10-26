import pandas as pd
import numpy as np
from DB.propaganda_db import DB
from typing import Dict, List
from datetime import datetime


def flatten(list_of_lists):
    return [el for a_list in list_of_lists for el in a_list]

def get_number_of_urls_published_before_source(url_to_date:  Dict[str, datetime], main_url:str):
    main_url_date = url_to_date[main_url]
    number_of_urls_published_before_source = 0
    for url, date in url_to_date.items():
        if date is None:
            continue
        print(date, main_url_date, date < main_url_date)
        if date < main_url_date:
            number_of_urls_published_before_source += 1
    return number_of_urls_published_before_source


def get_total_number_of_urls_in_level(url_to_level: Dict[str, int], max_level):
    """
    Total Number of urls in each level.
    :param url_to_level: dictionary, where key is url, and value is level
    :param max_level: number of levels to consider
    :return: list of size max_level
    """
    total_number_of_urls_in_level = [0] * max_level
    for _,level in url_to_level.items():
        if level>=0: #main_url has level = -1
            total_number_of_urls_in_level[level] +=1
    return total_number_of_urls_in_level





def get_time_hist(url_to_date: Dict[str, datetime], url_to_level: Dict[str, int], main_url: str, max_level: int) -> Dict:
    # we calculate time histogram for each level
    # by this we are saving as time information so connection
    main_url_date = url_to_date[main_url]

    minutes_hist_per_level = np.zeros((max_level, 24 * 60 * 2)).astype(int)  # 24h,60m, and 2 days
    hours_hist_per_level = np.zeros((max_level, 24 * 5)).astype(int)  # 24h and 5 days
    days_hist_per_level = np.zeros((max_level, 23)).astype(int)  # 23 days
    more_than_30_days_per_level = np.zeros(max_level)

    for url, date in url_to_date.items():
        if url == main_url:
            continue
        if date is None:
            # TODO: not sure what to do if the date is None
            continue
        day = (date - main_url_date).days
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
    return {"minute_hist": minutes_hist, "hour_hist": hour_hist, "day_hist": day_hist, "more_than_30_days": more_than_30_days_per_level.tolist()}


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


def get_date(url):
    return pd.to_datetime(db.get_date_published_url(url))


if __name__ == "__main__":
    db = DB("../DB/propaganda.db")
    main_url = "https://www.fondsk.ru/news/2020/03/25/borba-s-koronavirusom-i-bolshoj-brat-50441.html"
    links = db.get_tree(main_url)
    urls = get_unique_urls(links)

    url_to_date = {}

    url_to_level = get_level(links, main_url)
    max_level = 4

    for url in urls:
        date = get_date(url)
        url_to_date[url] = date
    print(url_to_date)
    minutes_hist, hour_hist, day_hist, more_than_30_days = get_time_hist(url_to_date, url_to_level, main_url, max_level)
