from os import path, makedirs

import requests
import pandas as pd
from selenium.webdriver import Chrome as Driver
# from selenium.webdriver import Firefox as Driver
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup as bs

from definitions import OUTPUT_DIR, STATES


class NoRecords(Exception): pass


class NoSuchMethod(Exception): pass


class AbstractCollectr:
    """
    Base DataFrame fields required for data passed through one of the collectrs:
        main_name.first_name    -> str: 'Bruce"
        main_name.last_name     -> str: 'Wayne'
        full_name               -> str: 'Bruce Wayne'
        city                    -> list if dicts:   [{city:'Gotham', state:'NY'}]
        aka                     -> list of full names as str:     ['Dark Knight']
        relatedTo               -> list of full names as str:     ['Alfred Pennyworth', 'Damian Wayne']
    DataFrame can have more than this, but these are required for validate_data() and check_relatives()
    """
    def __init__(self, person, base_url, **kwargs):
        self.site = type(self).__name__
        self.person = person
        self.base_url = base_url
        self.url = None
        self.soup = None
        self.df = pd.DataFrame()
        self.relatives = pd.DataFrame()
        self.test = kwargs.get('test', False)

        for k, v in kwargs.items():
            self.__setattr__(k, v)

        self.save_dir = path.join(OUTPUT_DIR, '{test}{first_name}_{last_name}'.format(
            first_name=self.person.first_name,
            last_name=self.person.last_name,
            test='__test__' if self.test else ''
        ))

    def __enter__(self):
        print(f'-- {self.site} --')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(self.df.index) > 0:
            self.save_csv()

    def save_csv(self):
        if not path.exists(self.save_dir):
            makedirs(self.save_dir)
        file_name = f'{self.site}.csv'

        self.df.to_csv(path.join(self.save_dir, file_name))

    def _add_relative(self, r):
        if 'state' not in r.index:
            r['state'] = input('\t\tPlease enter state: ').strip().title()

        if 'city' not in r.index:
            r['city'] = input('\t\tPlease enter City: ').strip().title()

        if 'middle_name' not in r.index:
            r['middle_name'] = input('\t\tPlease enter middle name: ').strip().title()

        try:
            r['check_family'] = bool(input('\t\tCheck relatives?: ').lower()[0] == 'y')
        except IndexError:
            r['check_family'] = False

        self.relatives = self.relatives.append(r, ignore_index=True)

    def
        (self):
        if len(self.df.index) == 0:
            return False

        if len(self.df.index) == 1:
            return True
        original_count = len(self.df.index)
        print(f'\t** Validate Records ({original_count}) **')
        for i, r in enumerate(self.df.iterrows()):
            top_city_index = r[1].top_city_states_best_match_index
            if top_city_index is None:
                top_city_index = 0

            city = r[1].top_city_states[top_city_index]
            try:
                same_state = (
                        (city.get('state', '').lower() == self.person.state.lower()) or
                        (city.get('state', '').lower() == STATES.get(self.person.state.upper(), '').lower()) or
                        (STATES.get(city.get('state', '').upper(), '').lower() == self.person.state.lower()))
                same_city = city.get('city', '').lower() == self.person.city.lower()
                same_city_state = same_city and same_state

            except AttributeError:
                same_city_state = False

            same_first = self.person.first_name.lower() == r[1]['main_name.first_name'].lower()
            same_last = self.person.last_name.lower() == r[1]['main_name.last_name'].lower()

            try:
                middle_as_first = self.person.middle_name.lower() == r[1]['main_name.first_name'].lower()
                middle_as_last = self.person.middle_name.lower() == r[1]['main_name.last_name'].lower()
            except AttributeError:
                middle_as_first = False
                middle_as_last = False

            aka = '; '.join(r[1].addl_full_names)
            if not same_city_state or not ((same_first or middle_as_first) and (same_last or middle_as_last)):

                msg = "{:{ocl}d}) Do you want to keep {full_name} of {city}, {state}?{aka}".format(
                    i + 1,
                    ocl=len(str(original_count)),
                    full_name=r[1].full_name,
                    city=city['city'],
                    state=city['state'],
                    aka=' (aka {aka})'.format(aka=aka) if len(aka) > 0 else '')

                try:
                    if input(f'\t{msg}\t').lower()[0] != 'y':
                        self.df.drop(i, inplace=True)
                except IndexError:
                    self.df.drop(i, inplace=True)
            else:
                msg = "{:{ocl}d})                kept {full_name} of {city}, {state}.{aka}".format(
                    i + 1,
                    ocl=len(str(original_count)),
                    full_name=r[1].full_name,
                    city=city['city'],
                    state=city['state'],
                    aka=' (aka {aka})'.format(aka=aka) if len(aka) > 0 else '')
                print(f'\t{msg}')

        print('\t** {count} record{s} found **\n'.format(count=len(self.df.index),
                                                         s='s' if len(self.df.index) != 1 else ''))
        return True

    def check_relatives(self, people=None):
        if not self.person.check_family:
            return False

        try:
            pr = pd.DataFrame([{'first_name': p.title().split()[0], 'last_name': p.title().split()[-1], 'middle_name': p.title().split()[1:-1]} for r in self.df['relatedTo'] for p in r])
        except KeyError:
            return False

        if len(pr.index) == 0:
            return False

        if people is not None:
            pr = pr[~((pr.first_name.isin(people.first_name)) & (pr.last_name.isin(people.last_name)))]

        if len(pr.index) == 0:
            return False

        orc = len(pr)
        print(f'\t** Check Relatives ({orc}) **')
        for i, r in enumerate(pr.iterrows()):
            try:
                msg = '{:{orc}d}) Would you like to add {first_name}{middle_name} {last_name}'.format(
                    i + 1,
                    orc=len(str(orc)),
                    first_name=r[1].first_name,
                    middle_name=' ' + ' '.join(r[1].middle_name) if len(r[1].middle_name) > 0 else '',
                    last_name=r[1].last_name
                )
                if input(f'\t{msg}?\t').lower()[0] == 'y':
                    self._add_relative(r[1])
            except IndexError:
                pass
        print('\t** {count} relative{s} found **\n'.format(count=len(self.relatives),
                                                           s='s' if len(self.relatives) != 1 else ''))
        return True

    def get_data(self): raise NoSuchMethod(f'"{self.site}" does not have function "get_data"')

    def get_soup(self): raise NoSuchMethod(f'"{self.site}" does not have function "get_soup"')


class RequestCollectr(AbstractCollectr):
    def __init__(self, person, base_url, **kwargs):
        super(RequestCollectr, self).__init__(person, base_url, **kwargs)

    def __enter__(self):
        super(RequestCollectr, self).__enter__()
        self.get_soup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(RequestCollectr, self).__exit__(exc_type, exc_val, exc_tb)

    def get_soup(self):
        with requests.get(self.url, headers={'User-Agent': 'Mozilla/5.0'}) as request:
            try:
                request.raise_for_status()
            except HTTPError as e:
                if '404 Client Error' in e.args[0]:
                    raise NoRecords(e.args[0])
                else:
                    raise e
            self.soup = bs(request.text, 'html.parser')


class SeleniumCollectr(AbstractCollectr):
    def __init__(self, person, base_url, **kwargs):
        super(SeleniumCollectr, self).__init__(person, base_url, **kwargs)

    def __enter__(self):
        super(SeleniumCollectr, self).__enter__()
        self.driver = Driver

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(SeleniumCollectr, self).__exit__(exc_type, exc_val, exc_tb)


