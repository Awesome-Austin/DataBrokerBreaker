from urllib.parse import urljoin
import logging

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd

from abstracts import RequestCollector, NoRecords
from definitions import TEST_PERSON


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logging.disable(logging.CRITICAL)

BASE_URL = 'https://radaris.com/'



class Radaris(RequestCollector):

    def __init__(self, person, **kwargs):

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
        try:
            self.get_data()
        except NoRecords:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Radaris, self).__exit__(exc_type, exc_val, exc_tb)

    def get_data(self):
        def _clean_data_(result):
            id = result.find(itemprop="url").get('href').split('/')[-1]

            given_name = result.find(itemprop='givenName')
            given_name = given_name.text.strip() if given_name is not None else ''

            middle_name = result.find(itemprop='additionalName')
            middle_name = middle_name.text.strip() if middle_name is not None else ''

            family_name = result.find(itemprop='familyName')
            family_name = family_name.text.strip() if family_name is not None else ''

            name_ = result.find(itemprop='name')
            name_ = name_.text.strip() if name_ is not None else ''

            age = result.find(class_='age')
            age = age.text.replace('age:', '').strip() if age is not None else ''

            address = {'@type': 'PostalAddress'}

            try:
                address['addressLocality'] = result.find(itemprop='AddressLocality').text.strip()
            except AttributeError as e:
                pass

            try:
                address['addressRegion'] = result.find(itemprop='AddressRegion').text.strip()
            except AttributeError as e:
                pass

            addl_name = result.find(class_='ka')
            addl_name = addl_name.text.split(":")[1].strip().split(', ') if addl_name is not None else ''

            related_to = result.find_all(itemprop='relatedTo')
            related_to = [{'name': r.find(itemprop='name').text.split(',')[0]}
                          for r in related_to if r.find(itemprop='name') is not None]

            url = urljoin(self.base_url, result.find(itemprop="url").get('href'))

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
                'additionalName': addl_name,
                'relatedTo': related_to,
                'url': url
            }

        logging.debug(self.url)
        res = requests.get(self.url)
        res.raise_for_status()
        soup = bs(res.content, 'html.parser')

        results = soup.find_all(lambda tag: tag.name == 'div' and tag.get('itemtype') == 'http://schema.org/Person')

        df = [_clean_data_(result) for result in results]
        self.data_from_website = pd.DataFrame(df)
        self.data_from_website.set_index('id', inplace=True)

    def validate_data(self):
        super(Radaris, self).validate_data()


if __name__ == '__main__':
    with Radaris(TEST_PERSON, test=True) as rad:
        rad.validate_data()
        rad.check_relatives()
