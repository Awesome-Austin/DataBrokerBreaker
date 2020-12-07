from urllib.parse import urljoin
import logging

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
            Takes in a search search_hit hit as a BeautifySoup tag and pulls out all the data to match the desired schema.

            :param search_hit:
            :return Dictionary: A dictionary with the cleaned data
            """
            id = search_hit.find(itemprop="url").get('href').split('/')[-1]

            given_name = search_hit.find(itemprop='givenName')
            given_name = given_name.text.strip() if given_name is not None else ''

            middle_name = search_hit.find(itemprop='additionalName')
            middle_name = middle_name.text.strip() if middle_name is not None else ''

            family_name = search_hit.find(itemprop='familyName')
            family_name = family_name.text.strip() if family_name is not None else ''

            name_ = search_hit.find(itemprop='name')
            name_ = name_.text.strip() if name_ is not None else ''

            age = search_hit.find(class_='age')
            age = age.text.replace('age:', '').strip() if age is not None else ''

            address = {'@type': 'PostalAddress'}

            try:
                address['addressLocality'] = search_hit.find(itemprop='AddressLocality').text.strip()
            except AttributeError as e:
                logging.debug(e)

            try:
                address['addressRegion'] = search_hit.find(itemprop='AddressRegion').text.strip()
            except AttributeError as e:
                logging.debug(e)

            aka = search_hit.find(class_='ka')
            aka = aka.text.split(":")[1].strip().split(', ') if aka is not None else ''

            related_to = search_hit.find_all(itemprop='relatedTo')
            related_to = [r.find(itemprop='name') for r in related_to if r.find(itemprop='name') is not None]
            related_to = [{'name': r.text.split(',')[0]} for r in related_to]

            url = search_hit.find(itemprop="url").get('href')
            url = urljoin(self.base_url, url)

            return {
                '@context': 'http://schema.org',
                '@type': 'Person',
                'id': id,
                'givenName': given_name,
                'middleName': middle_name,
                'familyName': family_name,
                'name': name_,
                'age': age,
                'address': address,
                'additionalName': aka,
                'relatedTo': related_to,
                'url': url
            }

        logging.debug(self.url)
        res = requests.get(self.url)
        res.raise_for_status()
        soup = bs(res.content, 'html.parser')

        search_results = soup.find_all(
            lambda tag: tag.name == 'div' and tag.get('itemtype') == 'http://schema.org/Person'
        )

        search_results = [_clean_search_hit(result) for result in search_results]
        self.data_from_website = pd.DataFrame(search_results)
        self.data_from_website.set_index('id', inplace=True)
        return True

    def validate_data(self):
        super(Radaris, self).validate_data()


if __name__ == '__main__':
    from tests import TEST_PERSON
    with Radaris(TEST_PERSON) as rad:
        pass
