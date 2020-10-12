#!/usr/bin/env python
import os
from datetime import datetime
import requests
import traceback
from serpapi.google_search_results import GoogleSearchResults
import json
import argparse
from graph import build_a_graph
from urls import URLs
from utils import get_hash_for_url
from utils import timeit
import distance
from lxml.html import fromstring
from colorama import init
from colorama import Fore, Back, Style
import PyPDF2
import textract
import binascii
from dateutil.relativedelta import relativedelta

# Init colorama
init()


# Read the serapi api key
f = open("serapi.key")
SERAPI_KEY = f.readline()
f.close()


def sanity_check(url):
    """
    Check if we should or not download this URL by
    applying different blacklists
    """
    # Blacklist of pages to ignore
    blacklist = {"robots.txt", "sitemap"}

    # The url_path is 'site.xml' in
    # https://www.test.com/adf/otr/mine/site.xml
    url_path = url.split("/")[-1]
    domain = url.split("/")[2]

    # Apply blacklists of the pages we dont want
    if url_path in blacklist:
        return False

    # Remove homepages
    # http://te.co has 3 splits
    # http://te.co/ has 4 splits
    if len(url.split("/")) == 3 or (len(url.split("/")) == 4 and url[-1] == "/"):
        return False

    # Delete all '.xml' pages
    if url_path.split(".")[-1] == "xml":
        return False

    # Delete twitter links that are not posts
    if "twitter" in domain:
        if "status" not in url:
            return False

    # Delete 4chan links that are not posts
    if "4chan" in domain:
        if "thread" not in url:
            return False

    # Google searches in books and the web includes the link to the
    # original search, so is kind of a loop sometimes.
    # if 'books.google.com' in domain:
    # return False

    return True


# @timeit
def trigger_api(search_leyword):
    """
    Access to the API of serapi

    The API can do
        Bing using BingSearchResults class
        Baidu using BaiduSearchResults class
        Yahoo using YahooSearchResults class
        Ebay using EbaySearchResults class
        Yandex using YandexSearchResults class
        GoogleScholar using GoogleScholarSearchResults class

    This api has as parameters
    "position": 8,
    "title": "COVID-19 и Мишель Фуко (некоторые мысли вслух ...",
    "link": "https://www.geopolitica.ru/article/covid-19-i-mishel-fuko-nekotorye-mysli-vsluh",
    "displayed_link": "www.geopolitica.ru › article › covid-...",
    "thumbnail": null,
    "date": "Apr 5, 2020",
    "snippet": "... проект ID2020 (почитать о нем можно здесь - https://www.fondsk.ru/news/2020/03/25/borba-s-koronavirusom-i-bolshoj-brat-50441.html).",
    "cached_page_link": "https://webcache.googleusercontent.com/search?q=cache:rrzBOTKH5BsJ:https://www.geopolitica.ru/article/covid-19-i-mishel-fuko-nekotorye-mysli-vsluh+&cd=8&hl=en&ct=clnk&gl=us"

    """
    try:
        # print(f' == Retriving results for {search_leyword}')
        params = {"engine": "google", "q": search_leyword, "google_domain": "google.com", "api_key": SERAPI_KEY}

        # Here we store all the results of all the search pages returned.
        # We concatenate in this variable
        all_results = []

        # Get first results
        client = GoogleSearchResults(params)
        results = client.get_dict()

        # Store this batch of results in the final list
        try:
            all_results.append(results["organic_results"])
            # Since the results came in batches of 10, get all the 'pages'
            # together before continuing
            amount_total_results = results["search_information"]["total_results"]
            # The amount of results starts with 1, ends with 10 if there are > 10
            amount_of_results_so_far = len(results["organic_results"])
            # print(f' == Total amount of results: {amount_total_results}')
            # print(f' == Results retrieved so far: {amount_of_results_so_far}')
        except KeyError:
            # There are no 'organic_results' for this result
            amount_total_results = 0
            amount_of_results_so_far = 0

        # Threshold of maxium amount of results to retrieve. Now 100.
        # Some pages can have 100000's
        max_results = 100

        # While we have results to get, get them
        while (amount_of_results_so_far < amount_total_results) and (amount_of_results_so_far < max_results):
            # print(' == Searching 10 more...')
            # New params
            params = {
                "engine": "google",
                "q": search_leyword,
                "google_domain": "google.com",
                "start": str(amount_of_results_so_far + 1),
                "api_key": SERAPI_KEY,
            }
            client = GoogleSearchResults(params)
            new_results = client.get_dict()
            # Store this batch of results in the final list
            try:
                all_results.append(new_results["organic_results"])
            except KeyError:
                # We dont have results. It can happen because search engines
                # report an amount of results that has a lot of
                # repetitions. So you can only access a part
                # print(f'Error accessing organic results.
                # Results: {new_results}')
                break

            amount_of_results_so_far += len(new_results["organic_results"])
            # print(f' == Results retrieved so far: {amount_of_results_so_far}')

        print(f"\tTotal amount of results retrieved: {amount_of_results_so_far}")
        # Store the results of the api for future comparison
        modificator_time = str(datetime.now()).replace(" ", "_")
        # write the results to a json file so we dont lose them
        if "http" in search_leyword:
            # we are searching a domain
            for_file_name = search_leyword.split("/")[2]
        else:
            # if a title, just the first word
            for_file_name = search_leyword.split(" ")[0]
        file_name_jsons = "results-" + for_file_name + "_" + modificator_time + ".json"
        if args.verbosity > 1:
            print(f"\tStoring the results of api in {file_name_jsons}")
        if not os.path.exists("results"):
            os.makedirs("results")
        with open(os.path.join("results", file_name_jsons), "w") as f:
            json.dump(results, f)

        return all_results

    except Exception as e:
        print("Error in trigger_api()")
        print(f"{e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
        return False


# @timeit
def downloadContent(url):
    """
    Downlod the content of the web page
    """
    try:
        # Download up to 5MB per page
        headers = {"Range": "bytes=0-5000000"}  # first 5M bytes
        # Timeout waiting for an answer is 15 seconds
        page_content = requests.get(url, timeout=15, headers=headers)
        text_content = page_content.text
        tree = fromstring(page_content.content)
        title = tree.findtext('.//title')
    except requests.exceptions.ConnectionError:
        print('Error in getting content')
        return (False, False, False)
    except requests.exceptions.ReadTimeout:
        print('Timeout waiting for the web server to answer. We ignore and continue')
        return (False, False, False)
    except Exception as e:
        print('Error getting the content of the web.')
        print(f'{e}')
        print(f'{type(e)}')
        return (False, False, False)

    url_hash = get_hash_for_url(url)

    try:
        timemodifier = str(datetime.now()).replace(" ", "_").replace(":", "_")
        file_name = "contents/" + url_hash + "_" + timemodifier + "-content.html"
        if args.verbosity > 1:
            print(f"\t\tStoring the content of url {url} in file {file_name}")
        file = open(file_name, "w")
        file.write(text_content)
        file.close()
        return (text_content, title, file_name)
    except Exception as e:
        print('Error saving the content of the webpage.')
        print(f'{e}')
        print(f'{type(e)}')
        return (False, False, False)


def url_in_content(url, content, content_file):
    """
    Receive a url and a content and try to see if the url is in the content
    Depends on the type of data
    """
    if content and 'HTML' in content[:60].upper():
        # print(f'{Fore.YELLOW} html doc{Style.RESET_ALL}')
        all_content = ''.join(content)
        if url in all_content:
            return True
    elif content and '%PDF' in content[:4]:
        # print(f'{Fore.YELLOW} pdf doc{Style.RESET_ALL}')
        # url_in_hex = binascii.hexlify(url.encode('ascii'))
        # text = textract.process(content_file, method='tesseract', language='eng')
        try:
            pdfReader = PyPDF2.PdfFileReader(content_file)
        except PyPDF2.utils.PdfReadError:
            return False
        except Exception as e:
            print(f"Error in pydf2 call. {e}")
            print(f"{type(e)}")
            print(traceback.format_exc())
            return False
        num_pages = pdfReader.numPages
        count = 0
        text = ""
        while count < num_pages:
            pageObj = pdfReader.getPage(count)
            count += 1
            text += pageObj.extractText()
        # text = text.replace('\x','')
        # print(text)
        if url in text:
            return True
    elif content:
        # print(f'{Fore.YELLOW} other doc{Style.RESET_ALL}')
        # print(content[:20])
        # We consider this what?
        return False
    else:
        return False


def convert_date(search_time, google_date):
    # Convert the date from '2 days ago' to  a real date, compared with the search time
    if google_date == None:
        return None

    splitted = google_date.split()

    if len(splitted) == 1 and splitted[0].lower() == 'today':
        return str(search_time.isoformat())
    elif len(splitted) == 1 and splitted[0].lower() == 'yesterday':
        date = search_time - relativedelta(days=1)
        return str(date.isoformat())
    elif splitted[1].lower() in ['mins', 'min', 'minutes', 'minute']:
        date = search_time - relativedelta(minutes=int(splitted[0]))
    elif splitted[1].lower() in ['hour', 'hours', 'hr', 'hrs', 'h']:
        date = search_time - relativedelta(hours=int(splitted[0]))
        return str(date.date().isoformat())
    elif splitted[1].lower() in ['day', 'days', 'd']:
        date = search_time - relativedelta(days=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['wk', 'wks', 'week', 'weeks', 'w']:
        date = search_time - relativedelta(weeks=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['mon', 'mons', 'month', 'months', 'm']:
        date = search_time - relativedelta(months=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ['yrs', 'yr', 'years', 'year', 'y']:
        date = search_time - relativedelta(years=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[0].lower() in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dec']:
        date = datetime.strptime(google_date, '%b %d, %Y')
        return str(date.isoformat())
    else:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to check is distribution pattern.", type=str, required=True)
    parser.add_argument("-p", "--is_propaganda", help="If the URL is propaganda . If absent, is not propaganda.", action="store_true")
    parser.add_argument(
        "-n", "--number_of_levels", help="How many 'ring' levels around the URL we are going to search. Defaults to 2.", type=int, default=2
    )
    parser.add_argument("-c", "--dont_store_content", help="Do not store the content of pages to disk", action="store_true", default=False)
    parser.add_argument("-v", "--verbosity", help="Verbosity level", type=int, default=0)
    parser.add_argument("-u", "--urls_threshold", help="Threshold distance between the content of two pages when searching with title", type=int, default=0.3)
    args = parser.parse_args()
    try:

        if args.verbosity > 1:
            print(f"Searching the distribution graph of URL {args.link}\n\n")

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
            (main_content, main_title, content_file) = downloadContent(args.link)
            URLs.store_content(args.link, main_content)

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
            link_type = 'link'

            # Get links to this URL (children)
            data = trigger_api(url)

            # Set the URL 'date_of_query' to now
            search_date = datetime.now()
            URLs.set_query_datetime(url, search_date)

            # From all the jsons, get only the links to continue
            # urls = []
            urls_to_date = {}
            if data:
                for page in data:
                    for result in page:
                        # dict for urls and dates
                        if 'date' in result:
                            urls_to_date[result['link']] = result['date']
                        elif 'snippet' in result and '—' in result['snippet'][:16]:
                            # First try to get it from the snippet
                            # Usually "Mar 25, 2020"
                            temp_date = result['snippet'].split('—')[0].strip()
                            urls_to_date[result['link']] = temp_date
                        else:
                            # Get none date for now. TODO: get the date from the content
                            urls_to_date[result['link']] = None
            else:
                print("The API returned False because of some error. Continue with next URL")
                continue

            # Set the publication datetime for the url
            if args.link == url:
                formated_date = convert_date(search_date, urls_to_date[url])
                URLs.set_publication_datetime(url, formated_date)

            if args.verbosity > 1:
                print(f"\tThere are {len(urls_to_date)} urls still to search.")

            for child_url in urls_to_date.keys():
                print(f"\tSearching for url {child_url}")

                # Check that the children was not seen before in this call
                if child_url in urls_to_search:
                    if args.verbosity > 2:
                        print(f"\t\tRepeated url: {child_url}")
                        continue

                if sanity_check(child_url):

                    # Get the content of the url and store it
                    # We ask here so we have the content of each child
                    if not args.dont_store_content:
                        (content, title, content_file) = downloadContent(child_url)

                    # Verify that the link is meaningful
                    if not url_in_content(url, content, content_file):
                        print(f"\t\tThe URL {url} is not in the content of site {child_url} {Fore.RED} Discarding.{Style.RESET_ALL}")
                        # Consider deleting the downloaded content from disk
                        continue
                    print(f"\t\tThe URL {url} IS in the content of site {child_url} {Fore.BLUE} Keeping.{Style.RESET_ALL}")

                    all_links.append([url, child_url])

                    # Add the children to the DB
                    URLs.set_child(url, child_url, search_date, link_type)

                    # The child should have the level of the parent + 1
                    urls_to_search_level[child_url] = urls_to_search_level[url] + 1
                    urls_to_search.append(child_url)

                    # Add this url to the DB. Since we are going to search for it
                    URLs.add_url(child_url)

                    # Store the content (after storing the child)
                    URLs.store_content(child_url, content)

                    if args.verbosity > 1:
                        print(f"\tAdding the URL {child_url} with level {urls_to_search_level[child_url]}")
                else:
                    failed_links.append(child_url)

        # Second we search for results using the title of the main URL
        print("\n\n==========Second Phase Search for Title=========")
        # Get links to this URL (children)
        data = trigger_api(main_title)
        link_type = 'title'

        # When we search for the title, we dont store the date of search 
        # or publication because it was already stored when we search
        # using the URL

        # From all the jsons, get only the links to continue
        urls = []
        try:
            if data:
                for page in data:
                    for result in page:
                        urls.append(result['link'])
            else:
                print("The API returned False because of some error. \
                        Continue with next URL")
        except KeyError:
            # There are no 'organic_results' in this result
            pass

        for child_url in urls:
            print(f"Analyzing url {child_url}")
            # Check that the children was not seen before in this call
            if child_url in urls_to_search:
                if args.verbosity > 2:
                    print(f"\tRepeated url: {child_url}. {Fore.RED} Discarding.{Style.RESET_ALL}")
                    continue

            if sanity_check(child_url):

                # Get the content of the url and store it
                # We ask here so we have the content of each child
                if not args.dont_store_content:
                    (content, title, content_file) = downloadContent(child_url)

                # Verify that the link is meaningful
                urls_distance = distance.compare_content(main_content, content)
                if urls_distance <= args.urls_threshold:
                    print(f"\tThe content of {args.link} has distance with {child_url} of : {urls_distance}. {Fore.RED}Discarding.{Style.RESET_ALL}")
                    # Consider deleting the downloaded content from disk
                    continue
                print(f"\tThe content of {args.link} has distance with {child_url} of : {urls_distance}. {Fore.BLUE}Keeping.{Style.RESET_ALL}")

                all_links.append([url, child_url])

                # Add the children to the DB
                URLs.set_child(url, child_url, search_date, link_type)

                # Add this url to the DB
                URLs.add_url(child_url)

                # Store the content (after storing the child)
                URLs.store_content(child_url, content)

                if args.verbosity > 1:
                    print(f"\tAdding the URL {child_url}")
            else:
                failed_links.append(child_url)

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
