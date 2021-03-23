from selenium import webdriver
import time
from datetime import datetime


class Firefox:
    def __init__(self):
        self.driver = webdriver.Firefox()

    def quit(self):
        self.driver.quit()

    def get_twitter_data(self, searched_phrase):
        url = f"https://twitter.com/search?q={searched_phrase}&src=typed_query"
        twitter_results = []
        seen_urls = set()
        search_date = datetime.now()
        self.driver.get(url)

        time.sleep(3)
        for scrolling_number in range(5):  # we will scroll 5 times full screen
            time.sleep(1.5)
            # print(f"Scrolling number {scrolling_number}")
            for i in range(1, 10):  # and take first 10 links for each scroll
                try:
                    date_element = self.driver.find_element_by_xpath(
                        f"/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/div[{i}]"
                        f"/div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a/time"
                    )
                    publication_date = date_element.get_attribute("datetime")
                    link_element = self.driver.find_element_by_xpath(
                        f"/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/div[{i}]"
                        f"/div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a"
                    )
                    text_element = self.driver.find_element_by_xpath(
                        f"/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/div[{i}]"
                        f"/div/div/article/div/div/div/div[2]/div[2]/div[2]/div[1]/div"
                    )
                    link = link_element.get_attribute("href")
                    if link not in seen_urls:
                        seen_urls.add(link)
                        twitter_results.append(
                            {
                                "child_url": link,
                                "search_date": search_date,
                                "publication_date": publication_date,
                                "content": text_element.text,
                                "title": None,
                            }
                        )
                        # print(f"{number_of_extracting_tweet} was successful", datetime, link)
                        # print("--------------")
                    else:
                        pass
                        # print("Repeated tweet")
                except:
                    # Sometimes there are ads
                    pass
            if len(twitter_results) == 0:  # if we didnt extract in the first scroll, there is nothing there
                break

            self.driver.execute_script("window.scrollTo(0, 1080)")
        # print(f"Total extracted tweets {len(seen_urls)}: {seen_urls}")
        return twitter_results
