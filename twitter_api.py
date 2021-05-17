import requests
import yaml
import urllib
import time
import datetime

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
    print(response.request.url)

    if response.status_code == 429:  # ttoo many requests
        time.sleep(2)
        response = requests.request("GET", search_url, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


def get_twitter_data(searched_phrase, is_url, published_date = None):
    twitter_results = []
    end_time = datetime.datetime.now()
    # if we know published_day, we search for published_date - year,
    # else for now() - 3 year
    if published_date is None:
        start_time = end_time - datetime.timedelta(days=3*365)
    else:
        start_time = end_time - datetime.timedelta(days=365)

    headers = create_headers()
    if is_url:
        url = urllib.parse.quote(searched_phrase)
        query_params = {
            "query": f"url : {url}",
            "max_results": 100,
            "tweet.fields": "author_id,public_metrics,created_at",
            "start_time": start_time.isoformat("T") + "Z",
        }
    else:
        query_params = {
            "query": f'"{searched_phrase}"',
            "max_results": 100,
            "tweet.fields": "author_id,public_metrics,created_at",
            "start_time": start_time.isoformat("T") +'Z'
        }
    json_response = connect_to_endpoint(headers, query_params)
    links_set = set()
    if json_response["meta"]["result_count"] != 0:
        for result in json_response["data"]:
            link = f"https://twitter.com/{str(result['author_id'])}/status/{str(result['id'])}"
            if link not in links_set:
                links_set.add(link)
                twitter_results.append(
                    {
                        "child_url": link,
                        "search_date": end_time,
                        "publication_date": result["created_at"],
                        "content": result["text"],
                        "title": None,
                    }
                )
    print(f"In total was found {len(twitter_results)}")

    return twitter_results

if __name__ == '__main__':
    r = get_twitter_data('https://www.fondsk.ru/news/2020/03/25/borba-s-koronavirusom-i-bolshoj-brat-50441.html', True)
    print(r)
