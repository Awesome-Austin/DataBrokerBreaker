import logging
import time
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup as bs
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd

from definitions import STATES, TEST_PERSON, SCROLL_PAUSE_TIME
from abstracts import SeleniumCollector, NoRecords

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

BASE_URL = 'https://www.mylife.com/'


class ChromeCrash(StaleElementReferenceException): pass


class MyLife(SeleniumCollector):
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
        def _get_data(hit):
            hit_name = hit.find(class_='hit-name')
            url = hit_name.get('href')
            hit_id = url.split('/')[-1]
            name = hit_name.get_text().split(',')[0].title()

            current_city = hit.find(class_='hit-location').get_text().upper()
            try:
                top_city_states = [a.get('title').upper() for a in
                                   hit.find(class_='hit-pastAddresses').find_all(class_='hit-values')]
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
                job = hit.find(class_='hit-work').find(class_='hit-values').get_text().title()
            except AttributeError:
                job = ''

            try:
                school = hit.find(class_='hit-high-school').find(class_='hit-values').get_text().title()
            except AttributeError:
                school = ''

            return {
                'id': hit_id,
                'first_name': name.split()[0],
                'last_name': name.split()[-1],
                'url': url,
                'full_name': name,
                'top_city_states': top_city_states,
                'top_city_states_best_match_index': top_city_states_best_match_index,
                'work': job,
                'school': school,
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
                        time.sleep(2)
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
                        time.sleep(2)
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
        s = bs(page_source, 'html.parser')
        self.df = pd.DataFrame([_get_data(hit) for hit in s.find_all(class_='ais-InfiniteHits-item')])
        self.df.set_index('id')
        return True

    def deep_data(self):
        def _deep_data(url):
            with self.driver() as driver:
                # print(url)
                driver.fullscreen_window()
                driver.get(url)
                # time.sleep(.5)
                txt = driver.page_source
            soup = bs(txt, 'html.parser')
            # print(soup.prettify())

            profile_data = json.loads(soup.find(type="application/ld+json").text)
            profile_data['id'] = profile_data.pop('@id').split('/')[-1]
            profile_data.pop('@context')
            profile_data.pop('@type')

            about = profile_data.pop('about')
            for k, v in about.items():
                profile_data[k] = v

            # print(profile_data)
            full_name = profile_data.pop('name')
            profile_data['first_name'] = full_name.split()[0]
            profile_data['last_name'] = full_name.split()[1]
            profile_data['full_name'] = full_name
            profile_data['city'] = {
                'city': profile_data['address']['addressLocality'],
                'state': profile_data['address']['addressRegion']
            }

            profile_data['reputation_score'] = soup.find_all(class_='profile-score-display-number')[1].text

            profile_data['alert'] = {a.text for a in soup.find_all(class_='ln-flags-item')}

            addresses = []
            for a in soup.find(class_='contact-section-addresses').find_all('a', href=True):
                u = a['href'].split('/')
                if 'address' in u[3]:
                    street, city, state, postal = u[3:]
                    addresses.append({
                        'street': street.replace('address-', '').replace("_", " "),
                        'city': city,
                        'state': state,
                        'postal_code': postal,
                        'url': a['href']
                    })

            profile_data['addresses'] = addresses

            profile_data['aka'] = profile_data.pop('alternateName')

            social = [
                (s.text, s['href']) for s in
                soup.find(class_='contact-section-socials').find_all('a', href=True)
            ]
            profile_data['social'] = social

            relatives = soup.find_all(class_='relative-section-item-details')
            profile_data['relatedTo'] = [{
                'name': r.find('a').get_text().title(),
                'url': urljoin(self.base_url, r.find('a').get('href')),
                'city': r.find('span').get_text().split(', ')[0].title(),
                'state': r.find('span').get_text().split(', ')[1].upper()
            } for r in relatives]

            neighbors = soup.find_all(class_='neighbors-section-item-details')
            profile_data['neighbors'] = [{
                'name': n.find('a').get_text().title(),
                'url': urljoin(self.base_url, n.find('a').get('href')),
                'city': [a.get_text() for a in n.find_all('span', {'class': ''})],
            } for n in neighbors]

            pics = soup.find(class_='photo-section-items').find_all('img')
            profile_data['pics'] = [p.get('data-src', None) for p in pics if p.get('data-src', None) is not None]

            return profile_data

        df = pd.DataFrame([_deep_data(df.url) for i, df in self.df.iterrows()])
        df.set_index('id', inplace=True)
        self.df = df

    def validate_data(self):
        super(MyLife, self).validate_data()
        self.deep_data()
        for i, p in self.df.iterrows():
            for pic in p.pics:
                self.download_file(pic, f'{p.id}_{i}')


if __name__ == '__main__':
    with MyLife(TEST_PERSON, test=True) as ml:
        ml.validate_data()
        ml.matching_relatives()
