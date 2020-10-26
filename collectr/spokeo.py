import json
from urllib.parse import urljoin
import logging

import pandas as pd
from pandas.io.json import json_normalize

from definitions import STATES, TEST_PERSON
from abstracts import RequestCollectr, NoRecords

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)

BASE_URL = 'https://www.spokeo.com'


class Spokeo(RequestCollectr):
    def __init__(self, person, **kwargs):
        super(Spokeo, self).__init__(person, BASE_URL, **kwargs)
        if self.person.state.upper() in STATES.keys():
            self.person.state = STATES[self.person.state.upper()].title()

        self.url = urljoin(
            self.base_url, '/'.join(['{} {}'.format(self.person.first_name, self.person.last_name),
                                     '{}'.format(self.person.state),
                                     '{}'.format(self.person.city if type(self.person.city) == str else '')
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
        def _set_1(soup):
            script = json.loads([tag for tag in soup.find(class_="list-view").find_all("div", {"class": 'panel'})
                                 if len(tag['class']) == 1][0].find("script").text)
            df = pd.DataFrame(script)
            df['id'] = df['url'].str.split('/').str[-1].str[1:]
            df.drop(columns=['@context', '@type'], inplace=True)
            df['homeLocation'] = [[a['address'] for a in d] for d in df['homeLocation']]
            df['additionalName'] = [[tuple(n.split()) for n in d] for d in df['additionalName']]
            df.set_index('id', inplace=True)
            return df

        def _set_2(soup):
            df = json_normalize(json.loads([
                                               tag.text.replace('var __PRELOADED_STATE__ = ', '') for tag in
                                               soup.find('div', {'id': 'root'}).find_all("script") if
                                               'var __PRELOADED_STATE__ = ' in tag.text][0])['people'])
            return df

        df = pd.merge(_set_1(self.soup), _set_2(self.soup), on='id', how='outer')
        df.set_index('id', inplace=True)
        df.rename(columns={'main_name.first_name': 'first_name',
                           'main_name.middle_name': 'middle_name',
                           'main_name.last_name': 'last_name'}, inplace=True)

        self.df = df


if __name__ == '__main__':
    with Spokeo(TEST_PERSON, test=True) as s:
        s.validate_data()
        s.check_relatives()
