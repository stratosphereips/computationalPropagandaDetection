#!/usr/bin/env python
import traceback
import argparse
from colorama import init
from colorama import Fore, Style
from DB.propaganda_db import DB


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to ask to the DB.", type=str, required=True)
    parser.add_argument("-L", "--links", help="List all the links.", type=str, required=False)
    parser.add_argument("-v", "--verbosity", help="Verbosity level", type=int, default=0)
    parser.add_argument("-d", "--path_to_db", help="DB file", type=str, default="DB/databases/propaganda.db")
    args = parser.parse_args()
    try:
        db = DB(args.path_to_db)

        if args.link:
            all_links, _ = db.get_tree(args.link)
            if args.verbosity > 0:
                date_query = db.get_date_of_query_url(args.link)
                date_url = db.get_date_of_query_url(args.link)
                title_url = db.get_title_url(args.link)
                content_snippet = db.get_content_snippet_from_url(args.link)
                print(f'Title: {title_url[0][0]}. Published: {date_url}. Quried: {date_query}. Snippet: {content_snippet}')
            if all_links:
                # Get info about the URL if asked
                previous_level = -1
                previous_parent = ""
                for data in all_links:
                    spaces = "  " * data[0]
                    if data[0] != previous_level:
                        print(f"{spaces}{Fore.RED}Level {data[0]}{Style.RESET_ALL}")
                        previous_level = data[0]
                    if previous_parent != data[1]:
                        print(f"{spaces}{Fore.CYAN}{data[1]}{Style.RESET_ALL}")
                        print(f"{spaces} {Fore.YELLOW}-> {data[2]}{Style.RESET_ALL}")
                    else:
                        print(f"{spaces} {Fore.YELLOW}-> {data[2]}{Style.RESET_ALL}")
                    previous_parent = data[1]
        elif args.links:
            pass

    except KeyboardInterrupt:
        # If ctrl-c is pressed
        pass
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
