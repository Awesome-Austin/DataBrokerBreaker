from urllib.parse import urljoin, urlsplit
import logging
import json

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd

from collectors import RequestCollector

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -  %(levelname)s -  %(message)s')
# logging.disable(logging.CRITICAL)

BASE_URL = 'https://radaris.com/'


class Radaris(RequestCollector):
    """
        A Class to represent an Radaris Search Collector.
        Radaris follows the content recommendations from http://schema.org, so minimal modifications to the data
            structure will be required.
    """
    def __init__(self, person, **kwargs):
        """
        :param person: Pandas.Series representing an individual
        """
        super(Radaris, self).__init__(person, BASE_URL, **kwargs)
        self.url = urljoin(self.base_url, 'ng/search?{}'.format(
            '&'.join(
                [s for s in ['{}'.format(f'ff={self.person.get("givenName", "").replace(" ", "+")}'),
                             '{}'.format(f'fl={self.person.get("familyName", "").replace(" ", "+")}'),
                             '{}'.format(f'fs={self.person.get("addressRegion", "").replace(" ", "+")}'),
                             '{}'.format(f'fc={self.person.get("addressLocality", "").replace(" ", "+")}')
                             ] if len(s) > 0]
            )))

    def __enter__(self):
        super(Radaris, self).__enter__()
        self.get_data()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Radaris, self).__exit__(exc_type, exc_val, exc_tb)

    def get_data(self):
        """
        Takes self.url (for a general Radaris search), scrapes the site data, and adds
            it to the self.data_from_website DataFrame
        :return: Boolean
        """
        def _clean_search_hit(search_hit):
            """
            Takes in a search_hit as a dictionary and pulls out all the data to match the desired schema.

            :param search_hit:
            :return Dictionary: A dictionary with the cleaned data
            """
            search_hit['url'] = search_hit.pop('@id')
            search_hit['@id'] = search_hit['url'].split('/')[-1]
            search_hit['middleName'] = search_hit.pop('additionalName', '')


            return search_hit

        logging.debug(self.url)
        res = requests.get(self.url)
        res.raise_for_status()
        soup = bs(res.content, 'html.parser')

        search_results = soup.find_all(
            lambda tag: tag.name == 'script' and tag.get('type') == 'application/ld+json'
        )[0].contents[0]

        search_results = json.loads(search_results)

        search_results = [_clean_search_hit(result) for result in search_results]
        self.data_from_website = pd.DataFrame(search_results)
        self.data_from_website.set_index('@id', inplace=True)
        return True

    def validate_data(self):
        super(Radaris, self).validate_data()


if __name__ == '__main__':
    from tests import TEST_PERSON
    with Radaris(TEST_PERSON) as rad:
        pass
