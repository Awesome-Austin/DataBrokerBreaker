import logging
import time
import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup as bs
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd

from definitions import STATES, SCROLL_PAUSE_TIME
from collectors import SeleniumCollector
from collectors.errors import NoRecords

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.disable(logging.CRITICAL)

BASE_URL = 'https://www.mylife.com/'

STATES = {STATE: ABBRIVIATION for ABBRIVIATION, STATE in STATES.items()}


class ChromeCrash(StaleElementReferenceException):
    pass


class MyLife(SeleniumCollector):
    """
        A Class to represent an MyLife Search Collector.
        MyLife follows the content recommendations from http://schema.org, so minimal modifications to the data
            structure will be required.
    """

    def __init__(self, person, **kwargs):
        """
        :param person: Pandas.Series representing an individual
        """
        super(MyLife, self).__init__(person, BASE_URL, **kwargs)
        self.url = urljoin(
            self.base_url,
            "pub-multisearch.pubview?search={first}+{last}".format(
                first=self.person.get('givenName', ''),
                last=self.person.get('familyName', ''))
        )

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
        Takes self.url (for a general MyLife search), scrapes the site data, and adds
            it to the self.data_from_website DataFrame.

        MyLife keeps its full data set on the page for the specific record, so self._gather_deep_data() can be used
            to pull that deeper data.
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
                address = search_hit.find(class_='hit-pastAddresses').find_all(class_='hit-values')
                address = list({a.text.upper().replace('.', '') for a in address})
            except AttributeError:
                address = list()

            # find the address that is most likely the current main address.
            try:
                address.insert(0, address.pop(address.index(current_city)))
            except ValueError:
                address.insert(0, current_city)

            address = [
                {
                    '@type': 'PostalAddress',
                    'addressLocality': locality.title(),
                    'addressRegion': region
                } for locality, region in [a.split(', ') for a in address]]

            work_location = {'@type': 'Place'}
            try:
                work_location['name'] = search_hit\
                    .find(class_='hit-work')\
                    .find(class_='hit-values')\
                    .get_text()\
                    .title()
            except AttributeError:
                work_location['name'] = ''

            alumni_of = {'@type': 'EducationalOrganization'}
            try:
                alumni_of['name'] = search_hit\
                    .find(class_='hit-high-school')\
                    .find(class_='hit-values')\
                    .get_text().title()
            except AttributeError:
                pass

            return {
                '@id': hit_id,
                '@type': 'Person',
                'name': ' '.join(name),
                'givenName': name[0],
                'middleName': ' '.join(name[1:-1]),
                'familyName': name[-1],
                'url': hit_url,
                'address': address,
                'workLocation': work_location,
                'alumniOf': alumni_of,
            }

        def _refine_search(search_str, options):
            """
            Takes a list of WebElements and a search string, looks for string in the text of each WebElement, and
                press the option if found. Returns Boolean for found status

            :param search_str: str of the desired option.
            :param options: list of WebElements from Beautify Soup that represents all of the available options.
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
            address_region = self.person.get('addressRegion', '')
            address_region = STATES.get(address_region.upper(), address_region.upper())
            region_options = driver\
                .find_element_by_class_name("STATE")\
                .find_elements_by_class_name("refinementList-text")

            if not _refine_search(address_region, region_options):
                return False

            # Narrow the search by pressing a City option
            address_locality = self.person.get('addressLocality').title()
            locality_options = driver\
                .find_element_by_class_name("CITY")\
                .find_elements_by_class_name("refinementList-text")

            if not _refine_search(address_locality, locality_options):
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
        self.data_from_website.set_index('@id', inplace=True)
        return True

    def _deep_data(self, url):
        """
        Takes a URL for a specific MyLife record, scrapes the JSON data and returns a dictionary.

        :param url: url for which a deeper set of data is to be gathered.
        :return:
        """
        def _nested_persons(persons):
            _persons = list()
            for person_ in persons:
                person_ = [r.text.split(', ') for r in person_.find_all(class_='default-text')]
                person = {'name': person_[0][0].title()}
                if len(person_[0]) == 2:
                    person['age'] = person_[0][1]

                if len(person_[1]) > 0:
                    person['addressLocality'] = person_[1][0].title()
                    if len(person_[1]) == 2:
                        person['addressRegion'] = person_[1][1].upper()

                _persons.append(person)
            return _persons

        with self.driver(self.DRIVER_DIR) as driver:
            driver.get(url)
            driver.fullscreen_window()
            time.sleep(2)
            txt = driver.page_source

        soup = bs(txt, 'html.parser')

        profile_data = soup.find(type="application/ld+json")
        if profile_data is None:
            self._raise_site_schema_change()
        profile_data = profile_data.string
        profile_data = json.loads(profile_data, strict=False)
        profile_data['@id'] = profile_data.pop('@id').split('/')[-1]

        try:
            about = profile_data.pop('about')
            for k, v in about.items():
                profile_data[k] = v
        except KeyError:
            pass

        name_ = profile_data.pop('name')
        profile_data['name'] = name_

        name_ = name_.split()
        profile_data['givenName'] = name_[0]
        profile_data['middleName'] = ' '.join(name_[1:-1])
        profile_data['familyName'] = name_[-1]

        if soup.find(class_='rep-vcard-score') is not None:
            profile_data['reputation_score'] = "{min}-{max}".format(
                min=soup.find(class_='rep-vcard-min').text,
                max=soup.find(class_='rep-vcard-max').text
            )

        address = list()
        address_ = soup.find_all(class_='card-address')
        for a in address_:
            street_address, locality_region_postal, *misc = [_.text for _ in a.find_all(class_='block-container')]
            address_locality, locality_region_postal = locality_region_postal.split(',')
            address_region, postal_code = locality_region_postal.split()
            address.append({
                'streetAddress': street_address,
                'addressLocality': address_locality,
                'addressRegion': address_region,
                'postalCode': postal_code,
            })

        profile_data['address'] = address

        personal_details = soup.find(class_='card-personal-details')
        if personal_details is not None:
            personal_details = personal_details.find_all(class_='item-container')
            personal_details = [detail.text.split(': ') for detail in personal_details]
            personal_details = [_ for _ in personal_details if len(_) == 2]
            personal_details = {detail.lower().replace(' ', '_'): value for
                                detail, value in personal_details if value != 'Add Info'}

            birth_date = personal_details.pop('date_of_birth')
            if len(birth_date) > 0:
                profile_data['birthDate'] = birth_date

            for key_, value_ in personal_details.items():
                profile_data[key_] = value_

        # Education
        schools_ = soup.find(class_='card-education')
        if schools_ is not None:
            schools = list()
            schools_ = schools_.find_all(class_='card-content')
            for school in schools_:
                school = [detail.text.split(': ') for detail in school.find_all(class_='item-container')]
                school = {detail.lower().replace(' ', '_'): value for
                          detail, value in school if value != 'Add Info'}

                if len(school) == 0:
                    continue

                school['@type'] = 'EducationalOrganization'
                school['name'] = school.pop('school')
                school['streetAddress'], school['addressLocality'] = school.pop('city').split(', ')
                schools.append(school)

        # Work
        employers = soup.find(class_='card-job')
        if employers is not None:
            works_for = list()
            employers = employers.find_all(class_='card-content')
            for employer in employers:
                employer = [detail.text.split(': ') for detail in employer.find_all(class_='item-container')]
                employer = {detail.lower().replace(' ', '_'): value for
                            detail, value in employer if value != 'Add Info'}

                if len(employer) == 0:
                    continue

                employer['@type'] = 'Organization'
                try:
                    employer['name'] = employer.pop('company')
                except KeyError:
                    continue

                if len(employer.get('city', '')) > 0:
                    employer['streetAddress'], employer['addressLocality'] = employer.pop('city').split(', ')

                works_for.append(employer)

            if len(works_for) > 0:
                profile_data['worksFor'] = works_for

        # Automobiles
        automobiles = soup.find(class_='card-auto')
        if automobiles is not None:
            owns = list()
            automobiles = automobiles.find_all(class_='card-content')
            for automobile in automobiles:
                automobile = [detail.text.split(': ') for detail in automobile.find_all(class_='item-container')]
                automobile = {detail.lower().replace(' ', '_'): value for
                              detail, value in automobile if value != 'Add Info'}

                if len(automobile) == 0:
                    continue

                automobile['@type'] = 'Product'
                automobile['model'] = ' '.join([
                    automobile.pop('year'),
                    automobile.pop('make'),
                    automobile.pop('model')
                ])
                owns.append(automobile)

            if len(owns) > 0:
                profile_data['owns'] = owns

        profile_data['relatedTo'] = _nested_persons(soup.find_all(class_='relative-container'))
        profile_data['neighbors'] = _nested_persons(soup.find_all(class_='neighbor-container'))

        # Photos
        profile_data['pictures'] = list({photo['src'] for photo in soup.find_all(class_='profile-picture-holder')})
        return profile_data

    def _gather_deep_data(self):
        """
        Gathers the data that is deeper within the website by calling self._deep_data(url) for each record found
            during the general search in self.get_data()
        """

        cleaned_data_from_website = list()

        for i, search_result in self.data_from_website.iterrows():
            cleaned_data_from_website.append(self._deep_data(search_result.url))

        cleaned_data_from_website = pd.DataFrame(cleaned_data_from_website)
        if len(cleaned_data_from_website) == 0:
            cleaned_data_from_website['@id'] = '0'
        cleaned_data_from_website.set_index('@id', inplace=True)
        self.data_from_website = cleaned_data_from_website

    def validate_data(self):
        self.person = super(MyLife, self).validate_data()
        if len(self.data_from_website) > 0:
            self._gather_deep_data()

        for record_id, record in self.data_from_website.iterrows():
            for i, picture in enumerate(record.get('pictures', list())):
                if not 'profile-placeholder' in picture:
                    self.download_file(picture, f'{i}_{record_id}')

        return self.person


if __name__ == '__main__':
    from tests import TEST_PERSON
    with MyLife(TEST_PERSON) as ml:
        pass
