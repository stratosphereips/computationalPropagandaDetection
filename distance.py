#!/usr/bin/env python

import Levenshtein
from bs4 import BeautifulSoup
import argparse
import traceback


def compare_content(content1, content2):
    """
    Compare the content of two pages
    """
    distance = Levenshtein.ratio(content1, content2)
    return distance


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--first_file", help="First file name to read and compare", type=str, required=True)
    parser.add_argument("-s", "--second_file", help="Second file name to read and compare.", type=str, required=True)
    parser.add_argument("-v", "--verbosity", help="Verbosity level", type=int, default=0)
    args = parser.parse_args()
    try:
        # file1_name = 'contents/politanalyze.com-1.content.html'
        # file2_name = 'contents/fondsk.ru.atlaq.com_23-content.html'

        file1 = open(args.first_file, 'r')
        file2 = open(args.second_file, 'r')

        # Read the lines
        file1_html = file1.readlines()
        file2_html = file2.readlines()

        # Get all the text together, since it comes in arrays
        file1_html_join = ''.join(file1_html)
        file2_html_join = ''.join(file2_html)

        # Get rid of all the tags, and keep the human readable text
        file1_content = BeautifulSoup(file1_html_join, features="lxml").get_text()
        file2_content = BeautifulSoup(file2_html_join, features="lxml").get_text()

        distance = Levenshtein.ratio(file1_content, file2_content)
        print(f'Distance between file {args.first_file} and {args.second_file} = {distance}')

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
