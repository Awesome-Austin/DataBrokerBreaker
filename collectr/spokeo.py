import json
from urllib.parse import urljoin
import logging

import pandas as pd
from pandas.io.json import json_normalize

from definitions import STATES, TEST_PERSON
from collectr._abstract import RequestCollectr, NoRecords

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
            self.clean_data()
        except NoRecords:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Spokeo, self).__exit__(exc_type, exc_val, exc_tb)

    def clean_data(self):
        def _set_1(soup):
            script = json.loads([tag for tag in soup.find(class_="list-view").find_all("div", {"class": 'panel'})
                                 if len(tag['class']) == 1][0].find("script").text)
            df = json_normalize(script)
            df['id'] = df['url'].str.split('/').str[-1].str[1:]
            df.drop(columns=['@context', '@type'], inplace=True)
            df.rename(columns={'main_name.first_name': 'first_name',
                               'main_name.middle_name': 'middle_name',
                               'main_name.last_name': 'last_name'}, inplace=True)
            df['homeLocation'] = [[a['address'] for a in d] for d in df['homeLocation']]
            df['relatedTo'] = [[n['name'] for n in d] for d in df['relatedTo']]
            df['additionalName'] = [[tuple(n.split()) for n in d] for d in df['additionalName']]
            df.set_index('id', inplace=True)
            return df

        def _set_2(soup):
            df = json_normalize(json.loads([
                                               tag.text.replace('var __PRELOADED_STATE__ = ', '') for tag in
                                               soup.find('div', {'id': 'root'}).find_all("script") if
                                               'var __PRELOADED_STATE__ = ' in tag.text][0])['people'])
            df.set_index('id', inplace=True)
            return df

        self.df = pd.merge(_set_1(self.soup), _set_2(self.soup), on='id', how='outer')

    def validate_records(self):
        if len(self.df.index) == 0:
            return False

        if len(self.df.index) == 1:
            return True

        print('\t** Validate Records **')
        for i, r in self.df.iterrows():
            top_city_index = r.top_city_states_best_match_index
            if top_city_index is None:
                top_city_index = 0

            city = r.top_city_states[top_city_index]
            if city['state'] in STATES.keys():
                city['state'] = STATES[city['state']].title()

            same_city_state = (city['city'].lower() == self.person.city.lower()
                               and city['state'].lower() == self.person.state.lower())

            same_first = self.person.first_name.lower() == r['main_name.first_name'].lower()
            same_last = self.person.last_name.lower() == r['main_name.last_name'].lower()

            try:
                middle_as_first = self.person.middle_name.lower() == r['main_name.first_name'].lower()
                middle_as_last = self.person.middle_name.lower() == r['main_name.last_name'].lower()
            except AttributeError:
                middle_as_first = False
                middle_as_last = False

            if not same_city_state or not ((same_first or middle_as_first) and (same_last or middle_as_last)):
                aka = '; '.join(r.addl_full_names)
                msg = "Do you want to keep {full_name} of {city}, {state}?{aka}".format(
                    full_name=r.full_name,
                    city=city['city'],
                    state=city['state'],
                    aka=' (aka {aka})'.format(aka=aka) if len(aka) > 0 else '')

                try:
                    if input(f'\t{msg}\t').lower()[0] != 'y':
                        self.df.drop(i, inplace=True)
                except IndexError:
                    self.df.drop(i, inplace=True)
        print('\t- {count} record{s} found'.format(count=len(self.df.index), s='s' if len(self.df.index) != 1 else ''))
        print()
        return True

    def check_relatives(self, people=None):
        if not self.person.check_family:
            return False

        try:
            pr = pd.DataFrame([relative.split() for relative in [p for r in self.df['relatedTo'] for p in r]],
                              columns=['first_name', 'last_name'])
        except KeyError:
            return False

        if people is not None:
            pr = pr[~((pr.first_name.isin(people.first_name)) & (pr.last_name.isin(people.last_name)))]

        if len(pr.index) == 0:
            return False

        print('\t** Check Relatives **')
        for i, r in pr.iterrows():
            try:
                msg = f'Would you like to add {r.first_name} {r.last_name}'
                if input(f'\t{msg}?\t').lower()[0] == 'y':
                    self._add_relative(r)
            except IndexError:
                pass
        print()
        return True


if __name__ == '__main__':
    with Spokeo(TEST_PERSON, test=True) as s:
        s.validate_records()
        s.check_relatives()
