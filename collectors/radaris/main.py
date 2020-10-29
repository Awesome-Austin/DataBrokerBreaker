from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs
import pandas as pd

from abstracts import RequestCollectr, NoRecords
from definitions import TEST_PERSON

BASE_URL = 'https://radaris.com/'


class Radaris(RequestCollectr):

    def __init__(self, person, **kwargs):

        super(Radaris, self).__init__(person, BASE_URL, **kwargs)
        # self.person.state = STATES.get(self.person.state.upper(), self.person.state).title()
        self.url = urljoin(self.base_url, 'ng/search?{}'.format(
            '&'.join(
                [s for s in ['{}'.format(f'ff={self.person.first_name}' if self.person.first_name is not None else ''),
                             '{}'.format(f'fl={self.person.last_name}' if self.person.last_name is not None else ''),
                             '{}'.format(f'fs={self.person.state}' if self.person.state is not None else ''),
                             '{}'.format(
                                 f'fc={self.person.city.replace(" ", "+")}' if self.person.city is not None else '')
                             ] if len(s) > 0])))

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
        res = requests.get(self.url)
        res.raise_for_status()
        soup = bs(res.content, 'html.parser')

        results = soup.find_all(lambda tag: tag.name =='div' and tag.get('itemtype') == 'http://schema.org/Person')

        df = []
        for result in results:
            df.append({
                'id': result.find(itemprop="url").get('href').split('/')[-1],
                'first_name': result.find(itemprop='givenName').text.strip(),
                'middle_name': result.find(itemprop='additionalName').text.strip(),
                'last_name': result.find(itemprop='familyName').text.strip(),
                'full_name': result.find(itemprop='name').text.strip(),
                'age':  result.find(class_='age').text.replace('age:', '').strip(),
                'city': {
                    'city': result.find(itemprop='AddressLocality').text.strip(),
                    'state': result.find(itemprop='AddressRegion').text.strip()
                },
                'aka': result.find(class_='ka').text.split(":")[1].strip().split(', '),
                'relatedTo': [r.find(itemprop='name').text.split(',')[0] for r in
                              result.find_all(itemprop='relatedTo')],
                'url': urljoin(self.base_url, result.find(itemprop="url").get('href'))
            })

        self.df = pd.DataFrame(df)
        self.df.set_index('id', inplace=True)

    def validate_data(self):
        super(Radaris, self).validate_data()


if __name__ == '__main__':
    with Radaris(TEST_PERSON, test=True) as rad:
        rad.validate_data()
        rad.matching_relatives()
