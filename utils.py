import hashlib
import time
import requests
from lxml.html import fromstring
from datetime import datetime
import PyPDF2


def get_hash_for_url(url):
    return hashlib.md5(url.encode()).hexdigest()


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if "log_time" in kw:
            name = kw.get("log_name", method.__name__.upper())
            kw["log_time"][name] = int((te - ts) * 1000)
        else:
            print(f"\t\033[1;32;40mFunction {method.__name__}() took {(te - ts) * 1000:2.2f}ms\033[00m")
        return result

    return timed


@timeit
def download_content(url, verbosity=False):
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
        if verbosity:
            print(f"\t\tStoring the content of url {url} in file {file_name}")
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
        # The while loop will read each page.
        count = 0
        text = ""
        num_pages = pdfReader.numPages
        # If there is more than 20 pages, read only 20 first - some pdf are pretty large,
        # so we dont want to read all of them
        while count < num_pages and count < 20:
            pageObj = pdfReader.getPage(count)
            count += 1
            text += pageObj.extractText()
        # removing all new lines and spaces, since PDF is read with OCR, and
        # there is some descrepency in the extraction
        text = text.replace("\n", "")
        text = text.replace(" ", "")
        if url in text:
            return True
    elif content:
        # print(f'{Fore.YELLOW} other doc{Style.RESET_ALL}')
        # print(content[:20])
        # We consider this what?
        return False
    else:
        return False
