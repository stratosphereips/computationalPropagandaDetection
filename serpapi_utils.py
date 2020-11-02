from serpapi.google_search_results import GoogleSearchResults
import json
import requests
import os
from datetime import datetime
import traceback
import hashlib
import PyPDF2
from lxml.html import fromstring


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
        # if args.verbosity > 1:
        #     print(f"\tStoring the results of api in {file_name_jsons}")
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
        title = tree.findtext(".//title")
    except requests.exceptions.ConnectionError:
        print("Error in getting content")
        return (False, False, False)
    except requests.exceptions.ReadTimeout:
        print("Timeout waiting for the web server to answer. We ignore and continue")
        return (False, False, False)
    except Exception as e:
        print("Error getting the content of the web.")
        print(f"{e}")
        print(f"{type(e)}")
        return (False, False, False)

    url_hash = get_hash_for_url(url)

    try:
        timemodifier = str(datetime.now()).replace(" ", "_").replace(":", "_")
        file_name = "contents/" + url_hash + "_" + timemodifier + "-content.html"
        # if args.verbosity > 1:
        #     print(f"\t\tStoring the content of url {url} in file {file_name}")
        file = open(file_name, "w")
        file.write(text_content)
        file.close()
        return (text_content, title, file_name)
    except Exception as e:
        print("Error saving the content of the webpage.")
        print(f"{e}")
        print(f"{type(e)}")
        return (False, False, False)


def url_in_content(url, content, content_file):
    """
    Receive a url and a content and try to see if the url is in the content
    Depends on the type of data
    """
    if content and "HTML" in content[:60].upper():
        # print(f'{Fore.YELLOW} html doc{Style.RESET_ALL}')
        all_content = "".join(content)
        if url in all_content:
            return True
    elif content and "%PDF" in content[:4]:
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
