from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import distance
from serpapi_utils import url_in_content

from colorama import Fore, Style


def convert_date(search_time, google_date):
    # Convert the date from '2 days ago' to  a real date, compared with the search time
    if google_date is None:
        return None

    try:
        date = str(parse(google_date).isoformat())  # what is if is a date "2020-05-13" or "08.31.2020"
        return date
    except:
        pass

    splitted = google_date.split()

    if len(splitted) == 1 and splitted[0].lower() == "today":
        return str(search_time.isoformat())
    elif len(splitted) == 1 and splitted[0].lower() == "yesterday":
        date = search_time - relativedelta(days=1)
        return str(date.isoformat())
    elif splitted[1].lower() in ["mins", "min", "minutes", "minute"]:
        date = search_time - relativedelta(minutes=int(splitted[0]))
        return str(date.date().isoformat())
    elif splitted[1].lower() in ["hour", "hours", "hr", "hrs", "h"]:
        date = search_time - relativedelta(hours=int(splitted[0]))
        return str(date.date().isoformat())
    elif splitted[1].lower() in ["day", "days", "d"]:
        date = search_time - relativedelta(days=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ["wk", "wks", "week", "weeks", "w"]:
        date = search_time - relativedelta(weeks=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ["mon", "mons", "month", "months", "m"]:
        date = search_time - relativedelta(months=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[1].lower() in ["yrs", "yr", "years", "year", "y"]:
        date = search_time - relativedelta(years=int(splitted[0]))
        return str(date.isoformat())
    elif splitted[0].lower() in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dec"]:
        date = datetime.strptime(google_date, "%b %d, %Y")
        return str(date.isoformat())
    else:
        return None


def get_dates_from_results(data):
    """
    Receive a data object from the serpapi API
    For each url search for a date in the results of the API
    If there is a field 'date' use it, if not search the field
    'snippet' and try to extract the date from there
    """
    urls_to_date = {}
    for page in data:
        for result in page:
            # dict for urls and dates
            if "date" in result:
                urls_to_date[result["link"]] = result["date"]
            elif "snippet" in result and "—" in result["snippet"][:16]:
                # First try to get it from the snippet
                # Usually "Mar 25, 2020"
                temp_date = result["snippet"].split("—")[0].strip()
                urls_to_date[result["link"]] = temp_date
            else:
                # Get none date for now. TODO: get the date from the content
                urls_to_date[result["link"]] = None
    return urls_to_date


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

    # Delete pdf files for now
    if ".pdf" in url_path:
        return False

    # Google searches in books and the web includes the link to the
    # original search, so is kind of a loop sometimes.
    # if 'books.google.com' in domain:
    # return False

    return True


def get_links_from_results(data):
    urls = []
    try:
        if data:
            for page in data:
                for result in page:
                    urls.append(result["link"])
        else:
            print(
                "The API returned False because of some error. \
                    Continue with next URL"
            )
    except KeyError:
        # There are no 'organic_results' in this result
        pass
    return urls


def check_url_in_content(child_url, parent_url, content, content_file):
    # Get the content of the url and store it
    # We ask here so we have the content of each child
    if not url_in_content(parent_url, content, content_file):
        print(f"\t\tThe URL {parent_url} is not in the content of site {child_url} {Fore.RED} Discarding.{Style.RESET_ALL}")
        # Consider deleting the downloaded content from disk
        return False

    print(f"\t\tThe URL {parent_url} IS in the content of site {child_url} {Fore.BLUE} Keeping.{Style.RESET_ALL}")
    return True


def check_text_similiarity(main_content, main_url, child_url, content, threshold):
    urls_distance = distance.compare_content(main_content, content)
    if urls_distance <= threshold:
        print(f"\tThe content of {main_url} has distance with {child_url} of : {urls_distance}. {Fore.RED}Discarding.{Style.RESET_ALL}")
        # Consider deleting the downloaded content from disk
        return False
    print(f"\tThe content of {main_url} has distance with {child_url} of : {urls_distance}. {Fore.BLUE}Keeping.{Style.RESET_ALL}")
    return True
