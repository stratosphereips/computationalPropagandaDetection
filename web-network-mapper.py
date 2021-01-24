#!/usr/bin/env python
from datetime import datetime
import traceback
import argparse
from urls import URLs
from colorama import init as init_colorama
from colorama import Fore, Style
import logging
from twitter_api import Firefox
from utils import (
    url_blacklisted,
    url_in_content,
    convert_date,
    get_links_from_results,
    get_dates_from_api_result_data,
    check_text_similiarity,
    process_data_from_api,
    add_child_to_db,
)
from serpapi_utils import downloadContent, trigger_api

# Init colorama
init_colorama()


# Read the serapi api key
f = open("serapi.key")
SERAPI_KEY = f.readline()
f.close()


def extract_and_save_twitter_data(driver, URLs, searched_string, parent_url, type_of_link):
    twitter_info = driver.get_twitter_data(searched_string)
    search_date = datetime.now()
    for one_tweet in twitter_info:
        add_child_to_db(
            URLs=URLs,
            child_url=one_tweet["link"],
            parent_url=parent_url,
            search_date=search_date,
            publication_date=one_tweet["published_date"],
            content=one_tweet["text"],
            link_type=type_of_link,
            title=None,
        )


def search_google_by_title(title, url, URLs):
    """
    Search google results in SerAPI by title
    - Process the results to extract data for each url
    - Store the results in the DB
    - Return list of results
    """
    # Use API to get links to this URL
    data, amount_of_results = trigger_api(title)

    # For each url in the results do
    if data:
        child_urls_found = process_data_from_api(data,
                                                 url,
                                                 URLs,
                                                 link_type='title',
                                                 content_similarity=True)
    return child_urls_found


def search_google_by_link(url, URLs):
    """
    Search google results in SerAPI by link
    - Process the results to extract data for each url
    - Store the results in the DB
    - Return list of results
    """
    # Use API to get links to this URL
    data, amount_of_results = trigger_api(url)

    # For each url in the results do
    if data:
        child_urls_found = process_data_from_api(data,
                                                 url,
                                                 URLs,
                                                 link_type='link')

        # Special situation to extract date of the main url
        # from the API. This is not available after asking
        # for the API
        # Search in the results for the main url
        for page in data:
            for result in page:
                child_url = result["link"]
                if child_url == url:
                    main_url_publication_date = get_dates_from_api_result_data(result)
                    formated_date = convert_date(main_url_publication_date)
                    URLs.set_publication_datetime(url, formated_date)

        return child_urls_found


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to check is distribution pattern.", type=str, required=True)
    parser.add_argument("-p", "--is_propaganda", help="If the URL is propaganda . If absent, is not propaganda.", action="store_true")
    parser.add_argument(
        "-n", "--number_of_levels", help="How many 'ring' levels around the URL we are going to search. Defaults to 2.", type=int, default=2
    )
    parser.add_argument("-c", "--dont_store_content", help="Do not store the content of pages to disk", action="store_true", default=False)
    parser.add_argument("-v", "--verbosity", help="Verbosity level", type=int, default=0)
    parser.add_argument(
        "-u", "--urls_threshold", help="Not Working this parameter now. Threshold distance between the content of two pages when searching with title", type=int, default=0.3
    )
    args = parser.parse_args()
    main_url = args.link

    # Always check the largest verbosity first
    #if args.verbosity >= 2:
        #logging.basicConfig(level=logging.DEBUG)
    #elif args.verbosity >= 1:
        #logging.basicConfig(level=logging.INFO)

    # driver = Firefox()

    try:

        print(f"Searching the distribution graph of URL {args.link}. Using {args.number_of_levels} levels.\n")

        # Get the URLs object
        URLs = URLs("DB/propaganda.db", args.verbosity)

        # Store the main URL as an url in our DB
        URLs.add_url(args.link, int(args.is_propaganda))
        (main_content, main_title, content_file, publication_date) = downloadContent(args.link)
        URLs.store_content(args.link, main_content)
        URLs.store_title(args.link, main_title)
        URLs.set_query_datetime(args.link, datetime.now())

        # Search by URLs, and by levels
        urls_to_search_by_level = {}
        urls_to_search_by_level[0] = [args.link]
        for level in range(args.number_of_levels):
            try:
                for url in urls_to_search_by_level[level]:
                    print(f"\n{Fore.CYAN}== Level {level}. Google search by links to {url}{Style.RESET_ALL}")
                    google_results_urls = search_google_by_link(url, URLs)
                    print(f"\n{Fore.CYAN}== Level {level}. Google search by title as {url}{Style.RESET_ALL}")
                    google_results_urls = search_google_by_title(main_title, url, URLs)

                    urls_to_search_by_level[level+1] = google_results_urls
            except KeyError:
                # No urls in the level
                pass

        # driver.quit()

        # print(f"Finished with all the graph of URLs. Total number of unique links are {len(all_links)}")
        # build_a_graph(all_links, args.link)

    except KeyboardInterrupt:
        # If ctrl-c is pressed, do the graph anyway
        # build_a_graph(all_links, args.link)
        pass
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
