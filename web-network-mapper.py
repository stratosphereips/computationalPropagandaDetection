#!/usr/bin/env python
import os
from datetime import datetime
import traceback
import argparse
from graph import build_a_graph
from urls import URLs
from colorama import init as init_colorama
from colorama import Fore, Style
import logging
from twitter_api import Firefox
from utils import (
    sanity_check,
    check_content,
    convert_date,
    get_links_from_results,
    get_dates_from_results,
    check_text_similiarity,
)
from serpapi_utils import downloadContent, trigger_api, get_hash_for_url

# Init colorama
init_colorama()


# Read the serapi api key
f = open("serapi.key")
SERAPI_KEY = f.readline()
f.close()


def add_child_to_db(URLs, child_url, parent_url, search_date, publication_date, link_type, content, title):
    # Add the children to the DB
    URLs.set_child(parent_url, child_url, search_date, link_type)
    # Store the date of the publication of the URL
    formated_date = convert_date(search_date, publication_date)
    URLs.set_publication_datetime(child_url, formated_date)
    # Add this url to the DB. Since we are going to search for it
    URLs.add_url(child_url)
    # Store the content (after storing the child)
    URLs.store_content(child_url, content)
    # Store the search date
    URLs.set_query_datetime(child_url, search_date)
    URLs.store_title(child_url, title)


def extract_and_save_twitter_data(driver, URLs, searched_string, parent_url, type):
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
            link_type=type,
            title=None,
        )


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
        "-u", "--urls_threshold", help="Threshold distance between the content of two pages when searching with title", type=int, default=0.3
    )
    args = parser.parse_args()
    main_url = args.link
    if args.verbosity == 1:
        logging.basicConfig(level=logging.INFO)
    if args.verbosity == 2:
        logging.basicConfig(level=logging.DEBUG)

    driver = Firefox()

    try:

        logging.info(f"Searching the distribution graph of URL {args.link}\n\n")

        # Get the URLs object
        URLs = URLs("DB/propaganda.db", args.verbosity)

        URLs.add_url(args.link, int(args.is_propaganda))

        # Keep only the urls
        urls_to_search = []
        urls_to_search.append(args.link)
        # Keep the urls and their levels
        # The level is how far away it is from the original URL
        urls_to_search_level = {}
        urls_to_search_level[args.link] = 0
        # We need a list so we can loop through it whil is changing and we
        # need a dictionary to keep the levels. Is horrible to need both!
        # But I dont know how to do better

        # Here we store all the pair of links as [link, link], so we can
        # build the graph later
        all_links = []

        # Links which failed sanity check
        failed_links = []

        # Get the content of the url and store it
        if not args.dont_store_content:
            (main_content, main_title, content_file, publication_date) = downloadContent(args.link)
            URLs.store_content(args.link, main_content)
            URLs.store_title(args.link, main_title)

        # First we search for results using the URL
        for url in urls_to_search:

            # If we reached the amount of 'ring' levels around the URL
            # that we want, then stop
            # We compared against the args.number_of_levels - 1 because
            # we always must ask and add the 'leaves' webpages
            if urls_to_search_level[url] > args.number_of_levels - 1:
                break

            print("\n==========================================")
            print(f"URL search level {urls_to_search_level[url]}. Searching data for url: {url}")
            link_type = "link"
            # Get links to this URL (children)
            data = trigger_api(url)
            # Set the URL 'date_of_query' to now
            search_date = datetime.now()

            urls_to_date = {}
            if data:
                urls_to_date = get_dates_from_results(data)
            else:
                print("The API returned False because of some error. Continue with next URL")
                continue

            # Set the publication datetime for the main url
            if args.link == url:
                formated_date = convert_date(search_date, urls_to_date[url])
                URLs.set_publication_datetime(url, formated_date)

            logging.info(f"\tThere are {len(urls_to_date)} urls still to search.")

            for child_url in urls_to_date.keys():

                print(f"\tSearching for url {child_url}")

                # Check that the children was not seen before in this call
                if child_url in urls_to_search:
                    logging.debug(f"\t\tRepeated url: {child_url}. {Fore.RED} Discarding. {Style.RESET_ALL} ")
                    continue

                if sanity_check(child_url):

                    if not args.dont_store_content:
                        (content, title, content_file, publication_date) = downloadContent(child_url)
                        if urls_to_date[child_url] is None:
                            urls_to_date[child_url] = publication_date

                    if check_content(child_url, url, content, content_file):
                        print("Extracting twitter data")
                        extract_and_save_twitter_data(driver, URLs, child_url, url, link_type)
                        print("Twitter data extracted. Continue with google search.")

                        add_child_to_db(
                            URLs=URLs,
                            child_url=child_url,
                            parent_url=url,
                            search_date=search_date,
                            publication_date=urls_to_date[child_url],
                            link_type=link_type,
                            content=content,
                            title=title,
                        )
                        # The child should have the level of the parent + 1

                        all_links.append([url, child_url])
                        urls_to_search_level[child_url] = urls_to_search_level[url] + 1
                        urls_to_search.append(child_url)

                        logging.info(f"\tAdding the URL {child_url} with level {urls_to_search_level[child_url]}")
                else:
                    failed_links.append(child_url)

        # Second we search for results using the title of the main URL
        print("\n\n==========Second Phase Search for Title=========")
        # Get links to this URL (children)
        link_type = "title"
        print("First lets extract Twitter data")
        extract_and_save_twitter_data(driver, URLs, main_title, main_url, "title")

        data = trigger_api(main_title)
        search_date = datetime.now()

        urls_to_date = {}
        if data:
            urls_to_date = get_dates_from_results(data)
        else:
            print("The API returned False because of some error. Continue with next URL")

        urls = get_links_from_results(data)
        for child_url in urls:
            print(f"Analyzing url {child_url}")
            # Check that the children was not seen before in this call
            if child_url in urls_to_search:
                logging.debug(f"\tRepeated url: {child_url}. {Fore.RED} Discarding.{Style.RESET_ALL}")
                continue
            if sanity_check(child_url):
                if not args.dont_store_content:
                    (content, title, content_file, publication_date) = downloadContent(child_url)
                    if urls_to_date[child_url] is None:
                        urls_to_date[child_url] = publication_date

                if check_text_similiarity(
                    main_content=main_content, content=content, main_url=main_url, child_url=child_url, threshold=args.urls_threshold
                ):
                    add_child_to_db(
                        URLs=URLs,
                        child_url=child_url,
                        parent_url=main_url,
                        search_date=search_date,
                        publication_date=urls_to_date[child_url],
                        link_type=link_type,
                        content=content,
                        title=title,
                    )

                    all_links.append([main_url, child_url])
                    logging.info(f"\tAdding the URL {child_url}")
            else:
                failed_links.append(child_url)

        driver.quit()

        print(f"Finished with all the graph of URLs. Total number of unique links are {len(all_links)}")
        build_a_graph(all_links, args.link)

        # Stored the removed URLs in a file
        if not os.path.exists("removed_urls"):
            os.makedirs("removed_urls")
        with open(os.path.join("removed_urls", get_hash_for_url(args.link)), "w") as f:
            f.write("\n".join(failed_links))

    except KeyboardInterrupt:
        # If ctrl-c is pressed, do the graph anyway
        build_a_graph(all_links, args.link)
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
