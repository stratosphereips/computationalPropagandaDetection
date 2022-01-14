#!/usr/bin/env python
from datetime import datetime
import traceback
import argparse
from urls import URLs
from os.path import isfile
from colorama import init as init_colorama
from colorama import Fore, Style
from utils import (
    convert_date,
    get_dates_from_api_result_data,
    add_child_to_db,
)
from serpapi_utils import trigger_api, process_data_from_api, downloadContent
from twitter_api import get_twitter_data
from vk_api import get_vk_data
import graph
from DB.create_db import create_main_db

# Init colorama
init_colorama()

# Read the serapi api key
f = open("credentials.yaml", "r")
SERAPI_KEY = f.readline()
f.close()

SEARCH_ENGINES = ["google"] #, "yandex", "yahoo", "bing"]  # , "baidu"]  # baidu seems really bad
COLORS = [Fore.CYAN, Fore.LIGHTGREEN_EX, Fore.MAGENTA, Fore.LIGHTBLUE_EX, Fore.GREEN, Fore.BLUE, Fore.LIGHTCYAN_EX,
          Fore.LIGHTMAGENTA_EX]


def update_urls_with_results(URLs, results):
    child_urls_found = []
    for result in results:
        child_urls_found.append(result["child_url"])
        add_child_to_db(
            URLs=URLs,
            child_url=result["child_url"],
            parent_url=result["parent_url"],
            search_date=result["search_date"],
            publication_date=result["publication_date"],
            content=result["content"],
            link_type=result["link_type"],
            title=result["title"],
            similarity=result["similarity"],
            clear_content=result["clear_content"],
        )
    return child_urls_found


def extract_and_save_twitter_data(URLs, searched_string, parent_url, type_of_link):
    """
    Get twitter posts that contain a certain string

    Receives: a string to search in twitter
    """
    publication_date = URLs.get_publication_datetime(parent_url)
    is_link = type_of_link == "link"
    twitter_result = get_twitter_data(searched_string, is_link, publication_date)
    # print(f'Results from Twitter: {twitter_result}')
    for result in twitter_result:
        result["parent_url"] = parent_url
        result["link_type"] = type_of_link
        result["similarity"] = None
        result["clear_content"] = None
    return update_urls_with_results(URLs, twitter_result)


def extract_and_save_vk_data(URLs, searched_string, parent_url, type_of_link):
    vk_results = get_vk_data(searched_string)
    if not vk_results:
        return []
    for result in vk_results:
        result["parent_url"] = parent_url
        result["link_type"] = type_of_link
        result["similarity"] = None
        result["clear_content"] = None
    return update_urls_with_results(URLs, vk_results)


def search_by_title(title, url, URLs, search_engine, threshold=0.3, max_results=100):
    """
    Search results in SerAPI by title
    - Current engines: ["google", "yandex"]
    - Process the results to extract data for each url
    - Store the results in the DB
    - Return list of results
    """

    # Use API to get links to this URL
    data = trigger_api(title, search_engine, max_results)
    child_urls_found = []
    if data:
        google_results = process_data_from_api(data, url, URLs, link_type="title", content_similarity=True,
                                               threshold=threshold, max_results_to_process=max_results)
        child_urls_found = update_urls_with_results(URLs, google_results)
    return child_urls_found


def search_by_link(url, URLs, search_engine, threshold=0.3, max_results=100):
    """
    Search google results in SerAPI by link
    - Process the results to extract data for each url
    - Store the results in the DB
    - Return list of results
    """

    # Use API to get links to this URL
    data = trigger_api(url, search_engine, max_results=max_results)
    child_urls_found = []
    # For each url in the results do
    if data:
        google_results = process_data_from_api(data, url, URLs, link_type="link", threshold=threshold,
                                               max_results_to_process=max_results)
        print("updating")
        child_urls_found = update_urls_with_results(URLs, google_results)
        print("finished update")

        # Special situation to extract date of the main url
        # from the API. This is not available after asking
        # for the API
        # Search in the results for the main url
        for result in data:
            child_url = result["link"]
            if child_url == url:
                main_url_publication_date = get_dates_from_api_result_data(result)
                formated_date = convert_date(main_url_publication_date)
                URLs.set_publication_datetime(url, formated_date)
                break

    return child_urls_found


def main(main_url, is_propaganda=False, database="DB/databases/propaganda.db", verbosity=0, number_of_levels=2,
         urls_threshold=0.3, max_results=100):
    try:
        print(f"Searching the distribution graph of URL {main_url}. Using {number_of_levels} levels.\n")
        if not isfile(database):
            create_main_db(database)
        # Get the URLs object
        URLs_object = URLs(database, verbosity)

        # Store the main URL as an url in our DB
        URLs_object.add_url(main_url, int(is_propaganda))
        (main_content, main_title, content_file, publication_date, clear_content) = downloadContent(main_url)
        print(f'Main title: {main_title}')

        URLs_object.store_content(main_url, main_content)
        URLs_object.store_clear_content(main_url, clear_content)
        URLs_object.store_title(main_url, main_title)
        URLs_object.set_query_datetime(main_url, datetime.now())
        URLs_object.set_publication_datetime(main_url, publication_date)

        # Search by URLs, and by levels
        urls_to_search_by_level = {0: [main_url]}
        for level in range(number_of_levels):
            # try:
            print(f"In level {level} were found {len(urls_to_search_by_level[level])} urls including original")
            for url in urls_to_search_by_level[level]:
                title = URLs_object.get_title_by_url(url)
                all_urls_by_urls, all_urls_by_titles = [], []
                # Search by link
                for i, engine in enumerate(SEARCH_ENGINES):
                    print(f"\n{COLORS[i]}== Level {level}. Search {engine} by LINKS to {url}{Style.RESET_ALL}")
                    results_urls = search_by_link(url, URLs_object, search_engine=engine,
                                                  threshold=urls_threshold, max_results=max_results)
                    all_urls_by_urls.extend(results_urls)
                twitter_results_urls = extract_and_save_twitter_data(URLs_object, url, url, "link")
                all_urls_by_urls.extend(twitter_results_urls)

                vk_results_urls = extract_and_save_vk_data(URLs_object, url, url, "link")
                all_urls_by_urls.extend(vk_results_urls)

                if title is not None:
                    print("TITLE ", title)
                    for color, engine in zip(COLORS, SEARCH_ENGINES):
                        print(f"\n{color}== Level {level}. Search {engine} by TITLE as {title}{Style.RESET_ALL}")
                        results_urls_title = search_by_title(title, url, URLs_object, search_engine=engine,
                                                             threshold=urls_threshold, max_results=max_results)
                        all_urls_by_titles.extend(results_urls_title)

                    twitter_results_urls_title = extract_and_save_twitter_data(URLs_object, title, url, "title")
                    all_urls_by_titles.extend(twitter_results_urls_title)
                    print(f"\n{Fore.GREEN}== Level {level}. VK search by title as {title}{Style.RESET_ALL}")
                    vk_results_urls_title = extract_and_save_vk_data(URLs_object, title, url, "title")
                    all_urls_by_titles.extend(vk_results_urls_title)

                urls_to_search_by_level[level + 1] = all_urls_by_urls
            # except KeyError:
            #     # No urls in the level
            #     pass
        # print(f"Finished with all the graph of URLs. Total number of unique links are {len(all_links)}")

    # except KeyboardInterrupt:
    #     # If ctrl-c is pressed, do the graph anyway
    #     # build_a_graph(all_links, args.link)
    #     pass
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
    # graph.create_date_centered(main_url, database, 2)
    # graph.create_domain_centered(main_url, database)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l", "--link", help="URL to check is distribution pattern.", type=str, required=True,
    )
    parser.add_argument(
        "-p", "--is_propaganda", help="If the URL is propaganda . If absent, is not propaganda.", action="store_true",
    )
    parser.add_argument(
        "-n", "--number_of_levels", help="How many 'ring' levels around the URL we are going to search. Defaults to 2.",
        type=int, default=2,
    )
    parser.add_argument(
        "-c", "--dont_store_content", help="Do not store the content of pages to disk", action="store_true",
        default=False,
    )
    parser.add_argument("-d", "--database", help="Path to database", type=str, default="DB/databases/propaganda.db")
    parser.add_argument("-v", "--verbosity", help="Verbosity level", type=int, default=0)
    parser.add_argument(
        "-u",
        "--urls_threshold",
        help="Not Working this parameter now. Threshold distance between the content of two pages when searching with title",
        type=float,
        default=0.3,
    )
    parser.add_argument("-nu", "--number_processed_urls",
                        help="Number of results to be processed when searching on an engine", type=int, default=100)
    parser.add_argument("-e", "--engines", help=f"What engines to use, currently possible (default) {SEARCH_ENGINES}",
                        type=str)
    parser.add_argument("-gt", "--graph_timewindow", type=int,
                        help="Number of years to show in graph generation, interval <-gt, today>", default=2)
    args = parser.parse_args()

    # choose what engines to use
    if args.engines:
        args_engines = args.engines.lower().split(',')
        for eng in args_engines:
            if eng not in SEARCH_ENGINES:
                print(
                    f"{Fore.RED}Searching in not implemented engine {eng}{Style.RESET_ALL}, "
                    f"choose from implemented engines {SEARCH_ENGINES}")
                raise NotImplemented
        SEARCH_ENGINES = args_engines
    # print(args)
    main(args.link, args.is_propaganda, args.database, args.verbosity, args.number_of_levels, args.urls_threshold,
         args.number_processed_urls)
