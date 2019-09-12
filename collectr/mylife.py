import logging
import requests
import time
from urllib.parse import urljoin
from os import path, makedirs

from bs4 import BeautifulSoup as bs
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd

from definitions import STATES, TEST_PERSON, SCROLL_PAUSE_TIME
from collectr._abstract import SeleniumCollectr, NoRecords

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

BASE_URL = 'https://www.mylife.com/'


class ChromeCrash(StaleElementReferenceException): pass


class MyLife(SeleniumCollectr):
    def __init__(self, person, **kwargs):
        super(MyLife, self).__init__(person, BASE_URL, **kwargs)
        self.url = urljoin(self.base_url, "pub-multisearch.pubview?search={first}+{last}".format(
            first=self.person.first_name,
            last=self.person.last_name))
        self.auto_scroll = kwargs.get('auto_scroll', True)
    def __enter__(self):
        try:
            super(MyLife, self).__enter__()
            self.get_data()
        except NoRecords:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(MyLife, self).__exit__(exc_type, exc_val, exc_tb)

    def get_data(self):
        def _get_data(s):
            hit_name = s.find(class_='hit-name')
            url = hit_name.get('href')
            hit_id = url.split('/')[-1]
            name = hit_name.get_text().split(',')[0].title()
            try:
                age = int(hit_name.get_text().split(',')[1])
            except IndexError:
                age = None

            current_city = s.find(class_='hit-location').get_text().upper()
            try:
                top_city_states = [a.get('title').upper() for a in
                                   s.find(class_='hit-pastAddresses').find_all(class_='hit-values')]
            except AttributeError:
                top_city_states = []

            try:
                top_city_states_best_match_index = top_city_states.index(current_city)
            except ValueError:
                top_city_states_best_match_index = len(top_city_states)
                top_city_states.append(current_city)

            top_city_states = [{'city': c.title(), 'state': s.upper()} for c, s in
                               [a.split(', ') for a in top_city_states]]

            try:
                relatives = [r.get('title') for r in s.find(class_='hit-relatives').find_all(class_='hit-values')]
            except AttributeError:
                relatives = []

            try:
                akas = [r.get('title').title() for r in
                        s.find(class_='hit-akas').find_all(class_='hit-values')]
            except AttributeError:
                akas = []

            try:
                job = s.find(class_='hit-work').find(class_='hit-values').get_text().title()
            except AttributeError:
                job = ''

            try:
                school = s.find(class_='hit-high-school').find(class_='hit-values').get_text().title()
            except AttributeError:
                school = ''

            rep_score = tuple([s.get_text() for s in s.find_all(class_='hit-reputation-score')])

            alert = [a.get_text() for a in s.find_all(class_='hit-alert') if a.get_text() != 'ALERT: ']

            picture_url = s.find(class_='profile-pic').get('src')
            if picture_url == '/global/img/profile-placeholder.png':
                picture_url = None

            return {
                'id': hit_id,
                'main_name.first_name': name.split()[0],
                'main_name.last_name': name.split()[-1],
                'relatedTo': relatives,
                'url': url,
                'full_name': name,
                'age': age,
                'top_city_states': top_city_states,
                'top_city_states_best_match_index': top_city_states_best_match_index,
                'addl_full_names': akas,
                'work': job,
                'reputation_score': rep_score,
                'school': school,
                'picture_url': picture_url,
                'alert': alert,
            }

        with self.driver() as driver:
            driver.fullscreen_window()
            driver.get(self.url)

            try:
                state = {v: k for (k, v) in STATES.items()}.get(self.person.state.upper(), self.person.state.upper())
                for option in driver.find_element_by_class_name("STATE").find_elements_by_class_name(
                        "refinementList-text"):
                    if state in option.text.upper():
                        option.click()
                        time.sleep(1)
                        break
                else:
                    return False
            except AttributeError:
                pass

            except StaleElementReferenceException as e:
                ChromeCrash(e)

            try:
                city = self.person.city.title()
                for option in driver.find_element_by_class_name("CITY").find_elements_by_class_name(
                        "refinementList-text"):
                    if city in option.text.title():
                        option.click()
                        time.sleep(1)
                        break
                else:
                    return False
            except AttributeError:
                pass

            except StaleElementReferenceException as e:
                ChromeCrash(e)

            if self.auto_scroll and len(driver.find_elements_by_class_name("ais-InfiniteHits-item")) > 15:
                last_height = driver.execute_script("return document.body.scrollHeight")
                while True:
                    # Scroll down to bottom
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(SCROLL_PAUSE_TIME)

                    # Calculate new scroll height and compare with last scroll height
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

            page_source = driver.page_source

        hits = bs(page_source, 'html.parser').find_all(class_="ais-InfiniteHits-item")
        self.df = pd.DataFrame([_get_data(hit) for hit in hits])
        return True

    def validate_data(self):
        super(MyLife, self).validate_data()
        for i, p in self.df.iterrows():
            if p.picture_url:
                pic_dir = path.join(self.save_dir, self.site)
                if not path.exists(pic_dir):
                    makedirs(pic_dir)

                with open(path.join(pic_dir, f'{p.id}.jpg'), 'wb') as f:
                    res = requests.get(p.picture_url, allow_redirects=True, stream=True)
                    if not res.ok:
                        print(res)
                    for block in res.iter_content(1024):
                        if not block:
                            break
                        f.write(block)


if __name__ == '__main__':
    with MyLife(TEST_PERSON, test=True) as ml:
        ml.validate_data()

