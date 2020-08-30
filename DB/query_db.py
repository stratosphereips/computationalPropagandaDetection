#!/usr/bin/env python
import traceback
import argparse
from colorama import init
from colorama import Fore, Back, Style
from propaganda_db import DB


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--link", help="URL to ask to the DB.",
                        type=str, required=True)
    parser.add_argument("-L", "--links", help="List all the links.",
                        type=str, required=False)
    parser.add_argument("-v", "--verbosity", help="Verbosity level",
                        type=int, default=0)
    parser.add_argument("-d", "--path_to_db", help="DB file",
                        type=str, default='DB/propaganda.db')
    args = parser.parse_args()
    try:
        db = DB(args.path_to_db)

        if args.link:
            all_links = db.get_tree(args.link)
            previous_parent = ''
            for result in all_links:
                if previous_parent == result[0]:
                    print(f'\t{Fore.YELLOW}-> {result[1]}{Style.RESET_ALL}')
                else:
                    print(f'{Fore.CYAN}{result[0]}{Style.RESET_ALL}')
                    print(f'\t{Fore.YELLOW}-> {result[1]}{Style.RESET_ALL}')
                    previous_parent = result[0]
        elif args.links:
            pass

    except KeyboardInterrupt:
        # If ctrl-c is pressed
        pass
    except Exception as e:
        print(f"Error in main(): {e}")
        print(f"{type(e)}")
        print(traceback.format_exc())
