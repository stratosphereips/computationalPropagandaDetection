import requests
import yaml
import urllib
import time
from datetime import datetime
from colorama import Fore, Style

#
with open("credentials.yaml", "r") as f:
    TWITTER_KEY = yaml.load(f, Loader=yaml.SafeLoader)["twitter"]

search_url = "https://api.twitter.com/2/tweets/search/all"


# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields


def create_headers():
    headers = {
        "Authorization": "Bearer {}".format(TWITTER_KEY),
        "Content-type": "text/plain; charset=ISO-8859-1",
    }
    return headers


def connect_to_endpoint(headers, params):
    response = requests.request("GET", search_url, headers=headers, params=params)
    if response.status_code == 429:  # ttoo many requests
        time.sleep(2)
        response = requests.request("GET", search_url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def get_twitter_data(searched_phrase, is_url):
    twitter_results = []
    search_date = datetime.now()

    headers = create_headers()
    if is_url:
        url = urllib.parse.quote_plus(searched_phrase)
        query_params = {
            "query": f"url : {url}",
            "max_results": 100,
            "tweet.fields": "author_id,public_metrics,created_at",
        }
    else:
        query_params = {
            "query": f'"{searched_phrase}"',
            "max_results": 100,
            "tweet.fields": "author_id,public_metrics,created_at",
        }
    json_response = connect_to_endpoint(headers, query_params)
    print(f'\tDownloaded {json_response["meta"]["result_count"]} twitter content')
    amount_of_results = json_response["meta"]["result_count"]
    result_shown = 1
    links_set = set()
    if amount_of_results != 0:
        for result in json_response["data"]:
            print(
                f"\t{Fore.YELLOW}Result [{result_shown}] {Style.RESET_ALL} Processing twitter ID {result['id']}: {result['text']}"
            )
            link = f"https://twitter.com/{str(result['author_id'])}/status/{str(result['id'])}"
            if link not in links_set:
                links_set.add(link)
                twitter_results.append(
                    {
                        "child_url": link,
                        "search_date": search_date,
                        "publication_date": result["created_at"],
                        "content": result["text"],
                        "title": None,
                    }
                )
            result_shown += 1
    return twitter_results
