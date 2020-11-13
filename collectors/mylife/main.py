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
# logging.disable(logging.CRITICAL)

BASE_URL = 'https://www.mylife.com/'

STATES = {STATE: ABBRIVIATION for ABBRIVIATION, STATE in STATES.items()}


class ChromeCrash(StaleElementReferenceException):
    pass


class MyLife(SeleniumCollector):
    """
        A Class to represent an Spokeo Search Collector.
        Spokeo follows the content recommendations from http://schema.org, so minimal modifications to the data
            structure will be required.
    """

    def __init__(self, person, **kwargs):
        """
        :param person: Pandas.Series representing an individual
        """
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
        """

        :return: Boolean
        """
        def _clean_search_hit(search_hit):
            """
            Takes in a search result hit as a BeautifySoup tag and pulls out all the data to match the desired schema.

            :param search_hit:
            :return Dictionary: A dictionary with the cleaned data
            """

            hit_name = search_hit.find(class_='hit-name')
            hit_url = hit_name.get('href')
            hit_id = hit_url.split('/')[-1]
            name = hit_name.get_text().split(',')[0].title().split()

            current_city = search_hit.find(class_='hit-location').get_text().upper()

            # Find all Addresses for search result.

            try:
                top_city_states = search_hit.find(class_='hit-pastAddresses').find_all(class_='hit-values')
                top_city_states = list({address.text.upper().replace('.', '') for address in top_city_states})
            except AttributeError:
                top_city_states = list()

            # find the address that is most likely the current main address.
            try:
                top_city_states_best_match_index = top_city_states.index(current_city)

            except ValueError:
                top_city_states_best_match_index = len(top_city_states)
                top_city_states.append(current_city)

            top_city_states = [{'city': city_.title(), 'state': state_}
                               for city_, state_ in [address.split(', ') for address in top_city_states]]

            try:
                job = search_hit.find(class_='hit-work').find(class_='hit-values').get_text().title()
            except AttributeError:
                job = ''

            try:
                school = search_hit.find(class_='hit-high-school').find(class_='hit-values').get_text().title()
            except AttributeError:
                school = ''

            return {
                'id': hit_id,
                'name_': ' '.join(name),
                'main_name': {
                    'first_name': name[0],
                    'middle_name': ' '.join(name[1:-1]),
                    'last_name': name[-1],
                },
                'url': hit_url,
                'top_city_states': top_city_states,
                'top_city_states_best_match_index': top_city_states_best_match_index,
                'work': job,
                'school': school,
            }

        def _refine_search(search_str, options):
            """
            Takes a list of WebElements and a search string, looks for string in the text of each WebElement, and
                press the option if found. Returns Boolean for found status

            :param search_str: str of the desired option.
            :param options: list of WebElements from Beautify Soup that represents all of the avaiable options.
            :return:
            """
            search_str = search_str.upper()
            logging.info(f'Looking for \'{search_str}\'')
            try:
                for option in options:
                    option_text = option.text.upper()
                    logging.info(f'Option Checked: {option_text}')
                    if search_str in option_text:
                        option.click()
                        time.sleep(2)
                        logging.info(f'Option Selected: {option_text}')
                        return True
                else:
                    return False
            except AttributeError:
                return True
            except StaleElementReferenceException as e:
                ChromeCrash(e)

        with self.driver(executable_path=self.DRIVER_DIR) as driver:
            driver.get(self.url)

            """
            The CSS for the page doesn't show the State nor the City selector options if the page is too narrow,
                so we need to make sure the browser is open wide enough for the CSS to make those options visible. 
            """
            driver.fullscreen_window()

            # Refine the search by State
            state = STATES.get(self.person.state.upper(), self.person.state.upper())
            state_options = driver\
                .find_element_by_class_name("STATE")\
                .find_elements_by_class_name("refinementList-text")

            if not _refine_search(state, state_options):
                return False

            # Narrow the search by pressing a City option
            city = self.person.city.title()
            city_options = driver\
                .find_element_by_class_name("CITY")\
                .find_elements_by_class_name("refinementList-text")

            if not _refine_search(city, city_options):
                return False

            """
            The Page Loads dynamically, so we need to scroll down the page to show all the search results. It needs to
                be done in steps with a pause between movements to allow for loading. 
            Here it will first get the current location on the page, attempt to move down the page, and then check to
                see if the location changed.
            """


            if self.auto_scroll and len(driver.find_elements_by_class_name("ais-InfiniteHits-item")) > 15:
                current_height, new_height = 0, driver.execute_script("return document.body.scrollHeight")

                while new_height != current_height:
                    # Scroll down to the bottom of the page
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                    # Wait to load page
                    time.sleep(SCROLL_PAUSE_TIME)

                    # Calculate new scroll height and compare with last scroll height
                    current_height, new_height = new_height, driver.execute_script("return document.body.scrollHeight")

            page_source = driver.page_source
        page_soup = bs(page_source, 'html.parser')
        search_results = list(page_soup.find_all(class_='ais-InfiniteHits-item'))
        for i, search_result in enumerate(search_results):
            search_results[i] = _clean_search_hit(search_result)

        self.data_from_website = pd.DataFrame(search_results)
        self.data_from_website.set_index('id', inplace=True)
        return True

    def _deep_data(self, url):
        """
        Takes a URL for a specific MyLife record, scrapes the JSON data and returns a dictionary.

        :param url: url for which a deeper set of data is to be gathered.
        :return:
        """
        with self.driver(self.DRIVER_DIR) as driver:
            driver.get(url)
            driver.fullscreen_window()
            txt = driver.page_source

        soup = bs(txt, 'html.parser')

        profile_data = json.loads(soup.find(type="application/ld+json").string)
        profile_data['id'] = profile_data.pop('@id').split('/')[-1]

        about = profile_data.pop('about')
        for k, v in about.items():
            profile_data[k] = v

        name_ = profile_data.pop('name')
        profile_data['name'] = name_

        name_ = name_.split()
        profile_data['main_name'] = {
            'givenName': name_[0],
            'middle_name': ' '.join(name_[1:-1]),
            'familyName':  name_[-1],
        }
        profile_data['homeLocation'] = [profile_data.pop('address')]
        # profile_data['city'] = {
        #     'city': profile_data['address']['addressLocality'],
        #     'state': profile_data['address']['addressRegion']
        # }

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

    def _gather_deep_data(self):
        """
        Gathers the data that is deeper within the website.
        Automatically run after validating data.

        :return:
        """

        cleaned_data_from_website = list()

        for i, search_result in self.data_from_website.iterrows():
            cleaned_data_from_website.append(self._deep_data(search_result.url))

        cleaned_data_from_website = pd.DataFrame(cleaned_data_from_website)
        cleaned_data_from_website.set_index('id', inplace=True)
        self.data_from_website = cleaned_data_from_website

    def validate_data(self):
        super(MyLife, self).validate_data()
        self._gather_deep_data()
        for i, record in self.data_from_website.iterrows():
            for pic in record.pics:
                self.download_file(pic, f'{record.id}_{i}')


if __name__ == '__main__':
    # with MyLife(TEST_PERSON, test=True) as ml:
    #     ml.validate_data()
    #     if ml.matching_relatives():
    #         relatives = ml.relatives()

    ml = MyLife(TEST_PERSON, test=True)
    dd = ml._deep_data('https://www.mylife.com/john-smith/e781306924602')
    print()
