from selenium import webdriver
import time


class Firefox:
    def __init__(self):
        self.driver = webdriver.Firefox()

    def quit(self):
        self.driver.quit()

    def get_twitter_data(self, searched_phrase):
        url = f"https://twitter.com/search?q={searched_phrase}&src=typed_query"
        twitter_info = []
        seen_urls = set()
        self.driver.get(url)

        time.sleep(2)
        for scrolling_number in range(5):  # we will scroll 5 times full screen
            time.sleep(1)
            # print(f"Scrolling number {scrolling_number}")
            for i in range(1, 10):  # and take first 10 links for each scroll
                number_of_extracting_tweet = scrolling_number * 10 + i
                try:
                    date_element = self.driver.find_element_by_xpath(
                        f"/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/div[{i}]/div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a/time"
                    )
                    datetime = date_element.get_attribute("datetime")
                    link_element = self.driver.find_element_by_xpath(
                        f"/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/div[{i}]/div/div/article/div/div/div/div[2]/div[2]/div[1]/div/div/div[1]/a"
                    )
                    text_element = self.driver.find_element_by_xpath(
                        f"/html/body/div/div/div/div[2]/main/div/div/div/div[1]/div/div[2]/div/div/section/div/div/div[{i}]/div/div/article/div/div/div/div[2]/div[2]/div[2]/div[1]/div"
                    )
                    link = link_element.get_attribute("href")
                    if link not in seen_urls:
                        seen_urls.add(link)
                        twitter_info.append({"link": link, "text": text_element.text, "published_date": datetime})
                        # print(f"{number_of_extracting_tweet} was successful", datetime, link)
                        # print("--------------")
                    else:
                        pass
                        # print("Repeated tweet")
                except:
                    # Sometimes there are ads
                    pass
            self.driver.execute_script("window.scrollTo(0, 1080)")
        print(f"Total extracted tweets {len(seen_urls)}: {seen_urls}")
        return twitter_info
