from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import distance
import PyPDF2
import traceback

from colorama import Fore, Style


def convert_date(google_date):
    # Tries to identify a string as varios formats
    # using some heuristics
    # - Convert a string from '2 days ago' to a real date
    # - '1 day ago' or 'yesterday'
    # - recognize iso formt
    # For some dates it needs to compare
    # with the current search time

    search_time = datetime.now()

    if google_date is None:
        return None

    if type(google_date) == datetime:
        return google_date

    try:
        # what if it is a date "2020-05-13" or "08.31.2020"
        date = str(parse(google_date).isoformat())
        return date
    except Exception:
        pass

    splitted = google_date.split()

    try:
        if len(splitted) == 1 and splitted[0].lower() == "today":
            return str(search_time.isoformat())
        elif len(splitted) == 1 and splitted[0].lower() == "yesterday":
            date = search_time - relativedelta(days=1)
            return str(date.isoformat())
        elif len(splitted) == 1:
            # Catch here weird things like single words
            return None
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
        elif splitted[0].lower() in ["jan", "feb", "mar", "apr", "may",
                                     "jun", "jul", "ago", "sep", "oct",
                                     "nov", "dec"]:
            date = datetime.strptime(google_date, "%b %d, %Y")
            return str(date.isoformat())
        else:
            return None
    except IndexError as e:
        print(f'There were errors procesing {splitted}'
              'text in convert_date()')
        print(e)
        raise


def get_dates_from_api_result_data(result):
    """
    Receive an api data object from the serpapi API
    Search for a date in the results
    If there is a field 'date' use it, if not search the field
    'snippet' and try to extract the date from there
    """
    if "date" in result:
        date = convert_date(result["date"])
        print(f"\t\tDate found in the API results: {date}")
        return date
    elif "snippet" in result and "—" in result["snippet"][:16]:
        # First try to get it from the snippet
        # Usually "Mar 25, 2020"
        # Others that we are not finding now : 27 марта 2020
        date = convert_date(result["snippet"].split("—")[0].strip())
        print(f"\t\tDate found in the Snippet of the API results: {date}")
        return date
    else:
        # Get none date for now. TODO: get the date from the content
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


def url_blacklisted(url):
    """
    Check if we should or not download this URL by
    applying different blacklists.
    Do not download if:
    1. URL includes robots.txt
    2. URL includes sitemap
    3. URL includes *.xml
    4. URL is Twitter but not a post
    5. URL is 4chan but not a post
    6. URL includes *.pdf
    """
    # Blacklist of pages to ignore
    blacklist = {"robots.txt", "sitemap"}

    # The url_path is 'site.xml' in
    # https://www.test.com/adf/otr/mine/site.xml
    url_path = url.split("/")[-1]
    domain = url.split("/")[2]

    # Apply blacklists of the pages we dont want
    if url_path in blacklist:
        return True

    # Remove homepages
    # http://te.co has 3 splits
    # http://te.co/ has 4 splits
    # if len(url.split("/")) == 3 or (len(url.split("/")) == 4 and url[-1] == "/"):
    #    return True

    # Delete all '.xml' pages
    if url_path.split(".")[-1] == "xml":
        return True

    # Delete twitter links that are not posts
    if "twitter" in domain:
        if "status" not in url:
            return True

    # Delete 4chan links that are not posts
    if "4chan" in domain:
        if "thread" not in url:
            return True

    # Delete pdf files for now
    if ".pdf" in url_path:
        return True

    # Google searches in books and the web includes the link to the
    # original search, so is kind of a loop sometimes.
    # if 'books.google.com' in domain:
    # return False

    return False


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


def check_text_similiarity(main_content, main_url, child_url, content, threshold=0.3):
    urls_distance = distance.compare_content(main_content, content)
    if urls_distance <= threshold:
        print(
            f"\t\t{Fore.YELLOW}Different. {Style.RESET_ALL}The content of {main_url} "
            f"has distance with {child_url} of: {urls_distance}. {Fore.RED}Discarding.{Style.RESET_ALL}"
        )
        # Consider deleting the downloaded content from disk
        return False
    print(f"\t\tThe content of {main_url} has distance with {child_url} of : {urls_distance}. {Fore.BLUE}Keeping.{Style.RESET_ALL}")
    return True


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
        # Lets stop processing pdf for now, is too slow and not worth it
        return False

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


def add_child_to_db(URLs, child_url, parent_url, search_date, publication_date, link_type, content, title):
    """
    Add a webpage to the DB as child of a parent URL
    """
    # Add the children to the DB
    URLs.set_child(parent_url, child_url, search_date, link_type)
    # Store the date of the publication of the URL
    formated_date = convert_date(publication_date)
    URLs.set_publication_datetime(child_url, formated_date)
    # Add this url to the DB. Since we are going to search for it
    URLs.add_url(child_url)
    # Store the content (after storing the child)
    URLs.store_content(child_url, content)
    # Store the search date
    URLs.set_query_datetime(child_url, search_date)
    URLs.store_title(child_url, title)
