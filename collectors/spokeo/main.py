import json
import re
from urllib.parse import urljoin
import logging

import pandas as pd
from pandas.io.json import json_normalize

from definitions import STATES, TEST_PERSON
from abstracts import RequestCollector, NoRecords

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

BASE_URL = 'https://www.spokeo.com'


class Spokeo(RequestCollector):
    """
        A Class to represent an Spokeo Search Collector.
        Spokeo follows the content recommendations from http://schema.org, so minimal modifications to the data
            structure will be required.
    """
    def __init__(self, person, **kwargs):
        """:param person: Pandas.Series representing an individual"""
        super(Spokeo, self).__init__(person, BASE_URL, **kwargs)
        # Converts State Abbriviation to full state name, as Spokeo requires.
        if self.person.state.upper() in STATES.keys():
            self.person.state = STATES[self.person.state.upper()].title()

        # Generate the url for the search
        self.url = urljoin(
            self.base_url,
            '/'.join([
                f'{self.person.first_name} {self.person.last_name}',
                f'{self.person.state}',
                f"{self.person.city if type(self.person.city) == str else ''}"
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
        """ Search Spokeo for the given person. Spokeo splits the data into 2 parts, one hidden and one visible."""
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

            # search_results.set_index('id', inplace=True)
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
            return search_results

        visible_search_results = _visible_search_results()
        hidden_search_results = _hidden_search_results()

        all_search_results = pd.merge(visible_search_results, hidden_search_results, on='id', how='outer')
        all_search_results.set_index('id', inplace=True)

        self.data_from_website = all_search_results


if __name__ == '__main__':

    # with Spokeo(TEST_PERSON, test=True) as s:
    #     s.validate_data()
    #     if s.matching_relatives():
    #         relatives = s.relatives
    #         pass
    #     print()
    help(Spokeo)
