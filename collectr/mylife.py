import json
import re
from urllib.parse import urljoin
import logging

import pandas as pd
import time
from pandas.io.json import json_normalize
from selenium.webdriver.common.by import By

from definitions import STATES, TEST_PERSON, SCROLL_PAUSE_TIME
from collectr._abstract import SeleniumCollectr, NoRecords

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)


# STATES_ABR = {v: k for k, v in STATES.items()}
BASE_URL = 'https://www.mylife.com/'


class MyLife(SeleniumCollectr):
    def __init__(self, person, **kwargs):
        super(MyLife, self).__init__(person, BASE_URL, **kwargs)
        self.url = urljoin(self.base_url, "pub-multisearch.pubview?search={first}+{last}".format(
            first=self.person.first_name,
            last=self.person.last_name))

    def __enter__(self):
        try:
            super(MyLife, self).__enter__()
            self.clean_data()
        except NoRecords:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(MyLife, self).__exit__(exc_type, exc_val, exc_tb)

    def clean_data(self):
        data_pattern = \
            r'((.*),.(\d*))\s((.*),.(.*))\s(.{5}(.*))\s(.{12}(.*))\s(.{14}(.*))\s(.{6}(.*))\s(.{24}(.*).—.(.*))'
        re_data = re.compile(data_pattern)
        self.driver.fullscreen_window()
        self.driver.get(self.url)

        # # Get scroll height
        # last_height = self.driver.execute_script("return document.body.scrollHeight")
        #
        # while True:
        #     # Scroll down to bottom
        #     self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        #
        #     # Wait to load page
        #     time.sleep(SCROLL_PAUSE_TIME)
        #
        #     # Calculate new scroll height and compare with last scroll height
        #     new_height = self.driver.execute_script("return document.body.scrollHeight")
        #     if new_height == last_height:
        #         break
        #     last_height = new_height

        hits = self.driver.find_elements_by_class_name("ais-InfiniteHits-item")
        print()
        print(len(hits))
        print()
        for hit in hits:
            print(hit.get_attribute('innerHTML'))
            break


        # hits_matches = [re_data.findall(hit.text) for hit in hits]
        # for hit_matches in hits_matches:
        #     print(hit_matches)
        #     break
#

if __name__ == '__main__':
    with MyLife(TEST_PERSON, test=True) as ml:
        pass

