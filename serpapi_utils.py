from serpapi import GoogleSearch
import json
import requests
import os
from datetime import datetime
import traceback
import hashlib
from lxml.html import fromstring
from colorama import Fore, Style
import dateutil.parser
import re
import locale
from utils import url_in_content, check_text_similiarity, get_dates_from_api_result_data, url_blacklisted


# Read the serapi api key
f = open("serapi.key")
SERAPI_KEY = f.readline()
f.close()


def get_hash_for_url(url):
    return hashlib.md5(url.encode()).hexdigest()


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
    "snippet": "... проект ID2020 (почитать о нем можно здесь -
    https://www.fondsk.ru/news/2020/03/25/borba-s-koronavirusom-i-bolshoj-brat-50441.html).",
    "cached_page_link": "https://webcache.googleusercontent.com/search?q=cache:rrzBOTKH5BsJ:
    https://www.geopolitica.ru/article/covid-19-i-mishel-fuko-nekotorye-mysli-vsluh+&cd=8&hl=en&ct=clnk&gl=us"

    """
    try:
        # print(f' == Retriving results for {search_leyword}')
        params = {"engine": "google", "q": search_leyword, "google_domain": "google.com", "api_key": SERAPI_KEY}

        # Here we store all the results of all the search pages returned.
        # We concatenate in this variable
        all_results = []

        # Get first results
        client = GoogleSearch(params)
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
        max_results = 300

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
            client = GoogleSearch(params)
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

        print(f"\tTotal amount of results retrieved: {Fore.YELLOW}{amount_of_results_so_far}{Style.RESET_ALL}")
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
        # if args.verbosity > 1:
        #     print(f"\tStoring the results of api in {file_name_jsons}")
        if not os.path.exists("results"):
            os.makedirs("results")
        with open(os.path.join("results", file_name_jsons), "w") as f:
            json.dump(results, f)

        return all_results, amount_of_results_so_far

    except Exception as e:
        print("Error in trigger_api()")
        print(f"{e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
        return False, False


def parse_date_from_string(text):
    """
    Receive a string and give back a date
    object if we can find any date
    """
    years_to_monitor = ["2022", "2021", "2020", "2019"]
    # Even if we find a text date, after the conversion into object, it can be
    # that is wrong, for example the text 854.052020 triggers errors
    # So we need to control that de date is more than a minimum
    # However, we can't compare only dates with datetimes, so we need two
    control_min_date_naive = dateutil.parser.parse("2000/01/01")
    control_min_date = dateutil.parser.parse("2000/01/01T00:00:00+00:00")
    parsed_date = None

    def __parse_date_string(text_to_parse, min_date):
        parsed_date = None
        # First try in English
        try:
            parsed_date = dateutil.parser.parse(text_to_parse)
            if parsed_date < min_date:
                parsed_date = None
            return parsed_date
        except dateutil.parser._parser.ParserError:
            pass

        # Try in Russian
        try:
            locale.setlocale(locale.LC_ALL, "ru_RU")
            parsed_date = datetime.strptime(text_to_parse, "%d %b %Y")
            if parsed_date < min_date:
                parsed_date = None
            return parsed_date
        except dateutil.parser._parser.ParserError:
            pass
        except ValueError:
            pass

        # Other format/languague?

        return parsed_date

    for year_to_monitor in years_to_monitor:
        y_positions = [m.start() for m in re.finditer(year_to_monitor, text)]
        for y_position in y_positions:
            if y_position:

                if parsed_date is None:
                    # Is it like 2020-03-26T01:02:12+03:00?
                    year_first = text[y_position : y_position + 25]
                    parsed_date = __parse_date_string(year_first, control_min_date)

                if parsed_date is None:
                    # Is it like 2020/03/02? (slash doesnt matter)
                    year_first = text[y_position : y_position + 10]
                    parsed_date = __parse_date_string(year_first, control_min_date_naive)

                if parsed_date is None:
                    # Is it like 03/02/2020?
                    year_last = text[y_position - 6 : y_position + 4]
                    parsed_date = __parse_date_string(year_last, control_min_date_naive)

                if parsed_date is None:
                    # Is it like 'Mar. 27th, 2020'?
                    text_type_1 = text[y_position - 11 : y_position + 4]
                    parsed_date = __parse_date_string(text_type_1, control_min_date_naive)

                if parsed_date is None:
                    # Is it like 'November 10 2020'
                    text_type_1 = text[y_position - 12 : y_position + 4]
                    parsed_date = __parse_date_string(text_type_1, control_min_date_naive)

                if parsed_date is None:
                    # Is it like '27 марта 2020 г.'
                    text_type_1 = text[y_position - 9 : y_position + 4]
                    parsed_date = __parse_date_string(text_type_1, control_min_date_naive)

                if parsed_date is None:
                    # Is it like 2020/03/25?
                    text_type_1 = text[y_position : y_position + 9]
                    parsed_date = __parse_date_string(text_type_1, control_min_date_naive)

    return parsed_date


def extract_date_from_webpage(url, page_content):
    """
    Receive an URL and tree HTM: structure and try to find the date of
    publication in several heuristic ways
    """
    # If this is a specific website, suchas telegram or twitter,
    # do a better search
    tree = fromstring(page_content.content)
    title = tree.findtext(".//title")
    if title and "telegram" in title.lower():
        # Ignore telegram pages since we use Selenium for that
        return None
    elif title and "twitter" in title.lower():
        # Ignore Twitter pages since we use Selenium for that
        return None

    # First try to find the date in the url
    publication_date = parse_date_from_string(url)
    if publication_date:
        print(f"\t\tDate found in the URL: {publication_date}")
    else:
        # Second try to find the date in the content of the web
        publication_date = parse_date_from_string(page_content.text)
        if publication_date is None:
            print(f"\t\tDate found in the content of the page: {publication_date}")
    return publication_date


def downloadContent(url):
    """
    Downlod the content of the web page
    """
    try:
        # Download up to 5MB per page
        headers = {"Range": "bytes=0-5000000"}  # first 5M bytes
        # Timeout waiting for an answer is 15 seconds
        page_content = requests.get(url, timeout=10, headers=headers)
        text_content = page_content.text
        tree = fromstring(page_content.content)
        title = tree.findtext(".//title")
        # Get the date of publication of the webpage
        publication_date = extract_date_from_webpage(url, page_content)
    except requests.exceptions.ConnectionError:
        print(f"\t\t{Fore.MAGENTA}! Error in getting content due to a Connection Error. Port closed, web down?{Style.RESET_ALL}")
        return (False, False, False, False)
    except requests.exceptions.ReadTimeout:
        print(f"\t\t{Fore.MAGENTA}! Timeout waiting for the web server to answer.  We ignore and continue.{Style.RESET_ALL}")
        return (False, False, False, False)
    except Exception as e:
        print(f"\t\t{Fore.MAGENTA}! Error getting the content of the web.{Style.RESET_ALL}")
        print(f"\t\t{Fore.MAGENTA}! {e}{Style.RESET_ALL}")
        print(f"\t\t{type(e)}")
        return (False, False, False, False)

    url_hash = get_hash_for_url(url)

    try:
        # Store the file
        timemodifier = str(datetime.now()).replace(" ", "_").replace(":", "_")
        file_name = "contents/" + url_hash + "_" + timemodifier + "-content.html"
        # if args.verbosity > 1:
        #     print(f"\t\tStoring the content of url {url} in file {file_name}")
        file = open(file_name, "w")
        file.write(text_content)
        file.close()
    except Exception as e:
        print("\t\tError saving the content of the webpage.")
        print(f"\t\t{e}")
        print(f"\t\t{type(e)}")
        return (False, False, False)

    return (text_content, title, file_name, publication_date)


def process_data_from_api(data, url, URLs, link_type, content_similarity=False):
    """
    Receive data from SerAPI and process it
    It can be from results by link or title
    If we are asked to compare the content, we
    need the parent url to retrieve its content
    """
    # max_results_to_process = 1000000
    max_results_to_process = 200
    result_shown = 1
    results = []
    for page in data:
        for result in page:
            # To have some control on how many result we process
            max_results_to_process -= 1
            if max_results_to_process <= 0:
                break
            child_url = result["link"]
            print(f"\t{Fore.YELLOW}Result [{result_shown}] {Style.RESET_ALL} Processing URL {child_url}")
            result_shown += 1
            api_publication_date = get_dates_from_api_result_data(result)

            # Apply filters
            #
            # 1. No repeated urls
            if URLs.url_exist(child_url):
                print(f"\t\t{Fore.YELLOW}Repeated{Style.RESET_ALL} url: {child_url}. {Fore.RED} Discarding. {Style.RESET_ALL} ")
                continue

            # 2. Filter out some URLs we dont want
            if url_blacklisted(child_url):
                print(f"\t\t{Fore.YELLOW}Blacklisted{Style.RESET_ALL} url: {child_url}. {Fore.RED} Discarding. {Style.RESET_ALL} ")
                continue
            (content, title, content_file, content_publication_date) = downloadContent(child_url)

            # 3. Check similarity of content of pages
            if content_similarity:
                # Check the current content to the content of the parent url
                parent_content = URLs.get_content_by_url(url)
                if not check_text_similiarity(main_content=parent_content, content=content, main_url=url, child_url=child_url):
                    continue

            # If we dont have a publication date from the api
            # use the one from the content
            if not api_publication_date:
                publication_date = content_publication_date
            else:
                publication_date = api_publication_date

            # 3. Is the main url in the content of the page of child_url?
            # Dont do if we are also doing content similarity since that
            # is by title, not url
            if not content_similarity:
                if not url_in_content(url, content, content_file):
                    print(
                        f"\t\t{Fore.YELLOW}Not in content{Style.RESET_ALL}. The URL {url} is not in the content "
                        f"of site {child_url} {Fore.RED} Discarding.{Style.RESET_ALL}"
                    )
                    continue
                else:
                    print(f"\t\tThe URL {url} IS in the content of site {child_url} {Fore.BLUE} Keeping.{Style.RESET_ALL}")

            print(f"\t\tAdding to DB the URL {child_url}")
            results.append(
                {
                    "child_url": child_url,
                    "parent_url": url,
                    "search_date": datetime.now(),
                    "publication_date": publication_date,
                    "link_type": link_type,
                    "content": content,
                    "title": title,
                }
            )
    return results
