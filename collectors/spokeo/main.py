import json
import re
from urllib.parse import urljoin
import logging

import pandas as pd
from pandas import json_normalize

from definitions import STATES
from collectors import RequestCollector
from collectors.errors import NoRecords

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -  %(levelname)s -  %(message)s')
# logging.disable(logging.CRITICAL)

BASE_URL = 'https://www.spokeo.com'


class Spokeo(RequestCollector):
    """
        A Class to represent an Spokeo Search Collector.
        Spokeo follows the content recommendations from http://schema.org, so minimal modifications to the data
            structure will be required.
    """
    def __init__(self, person, **kwargs):
        """
        :param person: Pandas.Series representing an individual
        """
        super(Spokeo, self).__init__(person, BASE_URL, **kwargs)

        # Converts State Abbreviation to full state name, as Spokeo requires for their Search URL.
        person_region = self.person.get('addressRegion', '').upper()
        if person_region in STATES.keys():
            self.person['addressRegion'] = STATES[person_region].title()

        # Generate the url for the search
        self.url = urljoin(
            self.base_url,
            '/'.join([
                f'{self.person.givenName} {self.person.familyName}',
                f'{self.person.addressRegion}',
                f"{self.person.addressLocality if type(self.person.addressLocality) == str else ''}"
            ])).replace(' ', '-')

    def __enter__(self):
        try:
            super(Spokeo, self).__enter__()
            self.get_data()
        except NoRecords:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Spokeo, self).__exit__(exc_type, exc_val, exc_tb)

    def get_data(self):
        """
            Takes self.url (for a general Spokeo search), scrapes the site data, and adds
                it to the self.data_from_website DataFrame
            :return: Boolean
        """
        def _visible_search_results():
            """
            For each record found collect all that data held in the visible search results.
            It then extracts the json data and converts to a DataFrame.

            :return : DataFrame
            """

            json_types = self.soup.find(class_="list-view").find_all("script", {"type": "application/ld+json"})
            for tag in json_types:
                search_results = json.loads(tag.contents[0])
                if type(search_results) == list and search_results[0]['@type'] == "Person":
                    break
            else:
                self._raise_site_schema_change()
                return

            search_results = pd.DataFrame(search_results)

            # Create a field for Spokeo's internal record ID, needed to request record removal.
            search_results['id'] = search_results['url'].str.split('/').str[-1].str[1:]

            search_results.drop(
                inplace=True,
                columns=[
                    'relatedTo',
                    'homeLocation',
                ])

            return search_results

        def _hidden_search_results():
            """
            Find the data that is hidden within the site scripts.

            :return DataFrame:
            """
            re_json = re.compile("<script>var __PRELOADED_STATE__ = (.*)</script>")
            scripts = self.soup.find_all("script")
            for script in scripts:
                matches = re_json.findall(str(script))
                if len(matches) == 1:
                    search_results = json.loads(matches[0])['data']['people']
                    break
            else:
                self._raise_site_schema_change()
                return

            search_results = pd.DataFrame(search_results)
            name_fields = search_results.pop('main_name')
            # noinspection PyTypeChecker
            name_fields = json_normalize(name_fields)
            search_results['givenName'] = name_fields['first_name']
            search_results['middleName'] = name_fields['middle_name']
            search_results['familyName'] = name_fields['last_name']
            search_results.rename(
                inplace=True,
                columns={
                    'top_city_states': 'geo',
                    'family_members': 'relatedTo',
                })
            search_results['address'] = None

            for record_id, site_record in search_results.iterrows():
                # Update the address and geo coordinates to match schema.org
                geos = json_normalize(site_record['geo'])

                address = pd.DataFrame()
                address['addressLocality'] = geos.pop('city')
                address['addressRegion'] = geos.pop('state')
                address['postalCode'] = geos.pop('postal_code')

                geos['@type'] = 'GeoCoordinates'
                geos = geos.to_dict('records')

                # Move the most recent city to the top of the list
                geos.insert(0, geos.pop(site_record['top_city_states_best_match_index']))
                search_results.at[record_id, 'geo'] = geos

                address['@type'] = 'PostalAddress'
                address = address.to_dict('records')

                # Move the most recent city to the top of the list
                address.insert(0, address.pop(site_record['top_city_states_best_match_index']))
                search_results.at[record_id, 'address'] = address

                # Update 'relatedTo' to match schema.org
                related_to = [{'name': relation} for relation in site_record.get('relatedTo', [])]
                search_results.at[record_id, 'relatedTo'] = related_to

            search_results.drop(
                inplace=True,
                columns=[
                    'has_address',
                    'has_phone',
                    'has_email',
                    'directory_page_id',
                    'top_city_states_best_match_index',
                    'addl_full_names',
                    'full_name',
                ])

            return search_results

        # Search Spokeo for the given person. Spokeo splits the data into 2 parts, one hidden and one visible.
        visible_search_results = _visible_search_results()
        hidden_search_results = _hidden_search_results()

        all_search_results = pd.merge(visible_search_results, hidden_search_results, on='id', how='outer')
        all_search_results.set_index('id', inplace=True)

        self.data_from_website = all_search_results

    def validate_data(self):
        super(Spokeo, self).validate_data()
