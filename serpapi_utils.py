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
import numpy as np
import yaml
from utils import (
    url_in_content,
    check_text_similiarity,
    get_dates_from_api_result_data,
    url_blacklisted,
)
from newspaper import Article
from htmldate import find_date
from bs4 import BeautifulSoup
import re

try:
    with open("credentials.yaml", "r") as f:
        SERPAPI_KEY = yaml.load(f, Loader=yaml.SafeLoader)["serpapi"]
except FileNotFoundError:
    print(f'No credentials.yaml file. Stop')

import signal
from contextlib import contextmanager


class TimeoutException(Exception):
    pass


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def get_hash_for_url(url):
    return hashlib.md5(url.encode()).hexdigest()


def trigger_api(search_keyword, engine="google", max_results=100):
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
    if engine == "google":
        params = {
            "engine": "google",
            "q": search_keyword,
            "api_key": SERPAPI_KEY,
            # "tbm": "nws",
        }
    elif engine == "yandex":
        params = {
            "engine": "yandex",
            "text": search_keyword,
            "api_key": SERPAPI_KEY,
        }
    elif engine == "yahoo":
        params = {
            "engine": "yahoo",
            "p": search_keyword,
            "api_key": SERPAPI_KEY,
        }
    elif engine == "bing":
        params = {
            "engine": "bing",
            "q": search_keyword,
            "api_key": SERPAPI_KEY
        }
    elif engine == "baidu":
        params = {
            "engine": "baidu",
            "q": search_keyword,
            "api_key": SERPAPI_KEY
        }
    else:
        print(f"Error in trigger_api(): wrong engine: {engine}")
        return False, False


    try:

        # Here we store all the results of all the search pages returned.
        # We concatenate in this variable
        all_results = list()

        # Get first results
        client = GoogleSearch(params)
        results = client.get_dict()

        # Store this batch of results in the final list
        try:
            for result in results["organic_results"]:
                all_results.append(result)
            # all_results.append(results["organic_results"])
            # Since the results came in batches of 10, get all the 'pages'
            # together before continuing
            amount_total_results = results["search_information"]["total_results"]
            # The amount of results starts with 1, ends with 10 if there are > 10
            # print(f' == Total amount of results: {amount_total_results}')
            # print(f' == Results retrieved so far: {amount_of_results_so_far}')
        except KeyError:
            # There are no 'organic_results' for this result
            amount_total_results = 0

        # print(results["organic_results"])
        # Threshold of maxium amount of results to retrieve. Now 300.
        # Some pages can have 100000's

        # some APIs need search page instead of offset
        search_page = 0
        # While we have results to get, get them, updated to be more general
        while len(all_results) < max_results and "organic_results" in results.keys() and \
                len(results["organic_results"]):
            # this helps to stop looping if there are no more results, possible only when we know amount_total_results
            if isinstance(amount_total_results, int) and len(all_results) > amount_total_results:
                break

            search_page += 1
            # New params, adding search offset
            if engine == "google":
                params["start"] = str(len(all_results) + 1)
            elif engine == "yandex":
                params["p"] = search_page
            elif engine == "yahoo":
                params["b"] = str(len(all_results) + 1)
            elif engine == "bing":
                params["first"] = str(len(all_results) + 1)
            elif engine == "baidu":
                params["pn"] = str(len(all_results) + 1)

            client = GoogleSearch(params)
            results = client.get_dict()
            # Store this batch of results in the final list
            if "organic_results" in results.keys():
                for result in results["organic_results"]:
                    all_results.append(result)
            else:
                # We dont have results. It can happen because search engines
                # report an amount of results that has a lot of
                # repetitions. So you can only access a part
                break
            # print(results["organic_results"] if "organic_results" in results.keys() else "there are no results")
            # amount_of_results_so_far += len(results["organic_results"])
            # print(f' == Results retrieved so far: {amount_of_results_so_far}')

        print(f"\tTotal amount of results retrieved: {Fore.YELLOW}{len(all_results)}{Style.RESET_ALL}")
        # Store the results of the api for future comparison
        modificator_time = str(datetime.now()).replace(" ", "_")
        # write the results to a json file so we dont lose them
        if "http" in search_keyword:
            # we are searching a domain
            for_file_name = search_keyword.split("/")[2]
        else:
            # if a title, just the first word
            for_file_name = search_keyword.split(" ")[0]
        file_name_jsons = "results-" + for_file_name + "_" + modificator_time + ".json"
        if os.name == 'nt':
            file_name_jsons = "results-" + for_file_name + ".json"
        # print(file_name_jsons)
        # if args.verbosity > 1:
        #     print(f"\tStoring the results of api in {file_name_jsons}")
        if not os.path.exists("results"):
            os.makedirs("results")
        with open(os.path.join("results", file_name_jsons), "w") as f:
            # with open('results/test.json', "w") as f:
            json.dump(results, f)
        return all_results

    except Exception as e:
        print("Error in trigger_api()")
        print(f"{e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
        return False, False


def select_best_date_idx(date_idxs, text):
    regex_words = ["date.{0,4}publish", "publish.{0,4}date", "time.{0,4}publish", "publish.{0,4}time",
                   "article.{0,4}time", "article.{0,4}date", "date", "time"]
    title_start = re.search(r'<title.*>', text).end()
    title_end = re.search('</title>', text).start()
    title = text[title_start:title_end]
    regex_words.append(title[:int(len(title) / 3)])
    titles = np.asarray([[x.end() for x in re.finditer("|".join(regex_words), text, flags=re.IGNORECASE)]])
    distance_matrix = np.abs(np.asarray([date_idxs]).T - titles)
    final_idx = np.where(distance_matrix == np.min(distance_matrix))[0][0]
    return final_idx


def get_string_date(string, year):
    """
    Recieve relatively small block of string and year in in
    return ('day month_shortcut year', 'day month_shortcut year')  format, two possible dates found
    """

    def __day_month(a, b):
        """ figure out what is day and what is month, return string 'day month_shortcut' """
        if a[-2:].lower() in ["st", "nd", "rd", "th"]:
            # a is a number
            a = a[:-2]
        if b[-2:].lower() in ["st", "nd", "rd", "th"]:
            # b is a number
            b = b[:-2]
        if len(a) > len(b):
            return " ".join([b, a[:3]])
        else:
            return " ".join([a, b[:3]])

    date_list = re.split(r'[,<>/\-_ "\.%T]+', string)
    year_last, year_first = None, None
    try:
        year_idx = date_list.index(year)
    except ValueError:
        return None, None

    if year_idx > 2:
        day_month = __day_month(date_list[year_idx - 2], date_list[year_idx - 1])
        year_last = " ".join([day_month, year])
    if year_idx < len(date_list) - 2:
        day_month = __day_month(date_list[year_idx + 1], date_list[year_idx + 2])
        year_first = " ".join([day_month, year])
    return year_last, year_first


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

    def __parse_date_string(text_to_parse, min_date):
        # print('ttp\t', text_to_parse)
        parsed_date = None
        # First try in English or numbers
        try:
            parsed_date = dateutil.parser.parse(text_to_parse)
            if parsed_date < min_date:
                parsed_date = None
            # print(parsed_date)
            return parsed_date
        except dateutil.parser._parser.ParserError:
            pass
        except TypeError:
            pass

        # Try in Russian
        try:
            locale.setlocale(locale.LC_ALL, "ru_RU")
            parsed_date = datetime.strptime(text_to_parse, "%d %b %Y")
            # print(parsed_date)
            if parsed_date < control_min_date_naive:
                parsed_date = None
            return parsed_date
        except dateutil.parser._parser.ParserError:
            pass
        except ValueError:
            pass

        # Other format/languague?
        # print(parsed_date)
        return parsed_date

    possible_dates, possible_dates_position = [], []
    for year_to_monitor in years_to_monitor:
        y_positions = [m.start() for m in re.finditer(year_to_monitor, text)]
        for y_position in y_positions:
            # if y_position:
            # Is it like 2020-03-26T01:02:12+03:00 - the 'perfect format'
            year_first = text[y_position: y_position + 25]
            parsed_date = __parse_date_string(year_first, control_min_date)
            if parsed_date is not None:
                possible_dates.append(parsed_date)
                possible_dates_position.append(y_position)

            # Any format where year is last or first 'any other parsable format'
            # print(text[max(0, y_position - 50):y_position + 50])
            print(text[max(0, y_position - 50):min(y_position + 50, len(text))])
            year_last, year_first = get_string_date(text[max(0, y_position - 50):min(y_position + 50, len(text))],
                                                    year_to_monitor)
            if year_last is not None and parsed_date is None:
                parsed_date = __parse_date_string(year_last, control_min_date)
                if parsed_date is not None:
                    possible_dates.append(parsed_date)
                    possible_dates_position.append(y_position)

            if year_first is not None and parsed_date is None:
                parsed_date = __parse_date_string(year_first, control_min_date)
                if parsed_date is not None:
                    possible_dates.append(parsed_date)
                    possible_dates_position.append(y_position)

    if not possible_dates:
        return None
    else:
        return possible_dates[0]


def extract_date_from_webpage(url, page_content):
    """
    Receive an URL and tree HTM: structure and try to find the date of
    publication in several heuristic ways
    """
    # If this is a specific website, such as telegram or twitter,
    # do a better search
    tree = fromstring(page_content.content)
    title = tree.findtext(".//title")
    if title and "telegram" in title.lower():
        # Ignore telegram pages since we use Selenium for that
        return None
    elif title and "twitter" in title.lower():
        # Ignore Twitter pages since we use Selenium for that
        return None

    publication_date = parse_date_from_string(find_date(url))
    if publication_date is not None:
        return publication_date
        # First try to find the date in the url
    # publication_date = parse_date_from_string(url)
    # if publication_date:
    #     print(f"\t\tDate found in the URL: {publication_date}")
    # else:
    #     # Second try to find the date in the content of the web
    #     publication_date = parse_date_from_string(page_content.text)
    #     if publication_date is not None:
    #         print(f"\t\tDate found in the content of the page: {publication_date}")
    return publication_date


def downloadContent(url):
    """
    Downlod the content of the web page
    """
    # firstly use newspaper3k just to get publication date
    publication_date = None
    try:
        with time_limit(5):
            article = Article(url)
            article.download()
            article.parse()
            publication_date = article.publish_date
    except Exception as e:
        print("newspaper3k failed")
        pass
    try:
        print("downloading content - requests")
        # Download up to 5MB per page
        headers = {"Range": "bytes=0-5000000"}  # first 5M bytes
        # Timeout waiting for an answer is 15 seconds
        page_content = requests.get(url, timeout=10, headers=headers)
        text_content = page_content.text
        print(f"content downloaded, length = {len(text_content)}")
        bs_content = BeautifulSoup(page_content.text, features="lxml").get_text()
        # try:
        #     with time_limit(5):
        #         print("BS done")
        #         clear_content = re.sub(r'\s{2,}', r'\n', bs_content)
        #         print("1")
        #         clear_content = re.sub('\n(\S+\s?){1,6}\n', '\n\n\n', clear_content)
        #         print("2")
        #
        #         clear_content = re.sub('\n(\S+\s?){1,6}\n', '\n\n\n', clear_content)
        #         print("3")
        #
        #         clear_content = re.sub(r'\s{2,}', r'\n', clear_content)
        #         print("4")
        #
        # except TimeoutException as e:
        clear_content = bs_content

        print("content cleared")

        tree = fromstring(page_content.content)
        title = tree.findtext(".//title")
        # Get the date of publication of the webpage if newspaper3k didn't find any
        if publication_date is None:
            publication_date = parse_date_from_string(find_date(url))
        if publication_date is None:
            publication_date = find_date(text_content)
    except requests.exceptions.ConnectionError:
        print(
            f"\t\t{Fore.MAGENTA}! Error in getting content due to a Connection Error. Port closed, web down?{Style.RESET_ALL}"
        )
        return None, None, None, None, None
    except requests.exceptions.ReadTimeout:
        print(
            f"\t\t{Fore.MAGENTA}! Timeout waiting for the web server to answer.  We ignore and continue.{Style.RESET_ALL}"
        )
        return None, None, None, None, None
    except requests.exceptions.MissingSchema:
        print('Please add https:// or http:// to your URL')
        return None, None, None, None, None
    except Exception as e:
        print(
            f"\t\t{Fore.MAGENTA}! Error getting the content of the web.{Style.RESET_ALL}"
        )
        print(f"\t\t{Fore.MAGENTA}! {e}{Style.RESET_ALL}")
        print(f"\t\t{type(e)}")
        return None, None, None, None, None

    url_hash = get_hash_for_url(url)

    try:
        # Store the file
        timemodifier = str(datetime.now()).replace(" ", "_").replace(":", "_")
        file_name = "contents/" + url_hash + "_" + timemodifier + "-content.html"
        # if args.verbosity > 1:
        #     print(f"\t\tStoring the content of url {url} in file {file_name}")
        file = open(file_name, "w", encoding='utf-8')
        file.write(text_content)
        file.close()
    except Exception as e:
        print("\t\tError saving the content of the webpage.")
        print(f"\t\t{e}")
        print(f"\t\t{type(e)}")
        return None, None, None, None, None
        # return False, False, False, False

    return text_content, title, file_name, publication_date, clear_content


def process_data_from_api(data, url, URLs, link_type, content_similarity=False, threshold=0.3,
                          max_results_to_process=100):
    """
    Receive data from SerAPI and process it
    It can be from results by link or title
    If we are asked to compare the content, we
    need the parent url to retrieve its content
    """
    # print(f"LEN DATA PROCESS_DATA_FROM_API {len(data)}, {data}")
    # max_results_to_process = 1000000
    result_shown = 1
    results = []
    for result in data:

        # Check if there are any results back
        if not result:
            continue

        # To have some control on how many result we process
        max_results_to_process -= 1
        if max_results_to_process <= 0:
            break

        # this is because of baidu
        if "link" not in result.keys():
            continue

        child_url = result["link"]
        print(
            f"\t{Fore.YELLOW}Result [{result_shown}] {Style.RESET_ALL} Processing URL {child_url}"
        )
        result_shown += 1
        api_publication_date = get_dates_from_api_result_data(result)

        # Apply filters
        #
        # 1. No repeated urls
        if URLs.url_exist(child_url):
            print(
                f"\t\t{Fore.YELLOW}Repeated{Style.RESET_ALL} url: {child_url}. {Fore.RED} Discarding. {Style.RESET_ALL} "
            )
            continue

        # 2. Filter out some URLs we dont want
        if url_blacklisted(child_url):
            print(
                f"\t\t{Fore.YELLOW}Blacklisted{Style.RESET_ALL} url: {child_url}. {Fore.RED} Discarding. {Style.RESET_ALL} "
            )
            continue
        try:
            with time_limit(20):
                (content, title, content_file, content_publication_date, clear_content) = downloadContent(child_url)
        except TimeoutException as e:
            print("Timed out!")
            (content, title, content_file, content_publication_date, clear_content) = None, None, None, None, None

        # 3. Check similarity of content of pages
        if content_similarity:
            # Check the current content to the content of the parent url
            parent_content = URLs.get_content_by_url(url)
            parent_clear_content = URLs.get_clear_content_by_url(url)
            similarity = check_text_similiarity(
                main_content=parent_content,
                content=clear_content,
                main_url=url,
                child_url=child_url,
                threshold=threshold
            )
            if similarity is None:
                continue
        else:
            similarity = 1

        # If we dont have a publication date from the api
        # use the one from the content
        if not api_publication_date:
            publication_date = content_publication_date
        else:
            publication_date = api_publication_date

        # publication_date = content_publication_date
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
                print(
                    f"\t\tThe URL {url} IS in the content of site {child_url} {Fore.BLUE} Keeping.{Style.RESET_ALL}"
                )

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
                "similarity": similarity,
                "clear_content": clear_content,
            }
        )
    return results
