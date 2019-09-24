from os import path, makedirs

import requests
import pandas as pd
from selenium.webdriver import Chrome as Driver
# from selenium.webdriver import Firefox as Driver
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup as bs

from definitions import OUTPUT_DIR, STATES


class NoRecords(Exception):
    pass


class NoSuchMethod(Exception):
    pass


class AbstractCollectr:
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

        self.save_dir = path.join(OUTPUT_DIR, '{test}{givenName}_{familyName}'.format(
            givenName=self.person.givenName,
            familyName=self.person.familyName,
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
        if 'addressRegion' not in r.index:
            r['addressRegion'] = input('\t\tPlease enter state: ').strip().title()

        if 'addressLocality' not in r.index:
            r['addressLocality'] = input('\t\tPlease enter City: ').strip().title()

        if 'additionalName' not in r.index:
            r['additionalName'] = input('\t\tPlease enter middle name: ').strip().title()

        try:
            r['check_family'] = bool(input('\t\tCheck relatives?: ').lower()[0] == 'y')
        except IndexError:
            r['check_family'] = False

        self.relatives = self.relatives.append(r, ignore_index=True)

    def download_file(self, url, output_file_name):
        pic_dir = path.join(self.save_dir, self.site)
        if not path.exists(pic_dir):
            makedirs(pic_dir)

        try:
            res = requests.get(url, allow_redirects=True, stream=True)
            res.raise_for_status()
        except Exception as e:
            print(e)
            return False

        output_file_name += f".{res.headers['content-type'].split('/')[1]}"

        with open(path.join(pic_dir, output_file_name), 'wb') as f:
            for block in res.iter_content(1024):
                if not block:
                    break
                f.write(block)
        return True

    def validate_data(self):
        if len(self.df.index) == 0:
            return False

        if len(self.df.index) == 1:
            return True
        original_count = len(self.df.index)

        print(f'\t** Validate Records ({original_count}) **')
        for i, r in enumerate(self.df.iterrows()):

            address = r[1].address[r[1].get('top_city_states_best_match_index', 0)]
            address_region = address.get('addressRegion', '').lower()
            person_address_region = self.person.get('addressRegion', '').lower()

            same_state = (
                    (address_region == person_address_region) or
                    (address_region == STATES.get(person_address_region.upper(), '').lower()) or
                    (STATES.get(address_region.upper(), '').lower() == person_address_region))

            same_city = address.get('addressLocality', '').lower() == self.person.addressLocality.lower()

            # same_city_state = same_city and same_state

            same_first = self.person.givenName.lower() == r[1]['givenName'].lower()
            same_last = self.person.familyName.lower() == r[1]['familyName'].lower()

            middle_as_first = self.person.get('additionalName', '').lower() == r[1]['givenName'].lower()
            middle_as_last = self.person.get('additionalName', '').lower() == r[1]['familyName'].lower()

            aka = '; '.join(r[1].get('addl_full_names', []))
            if not (same_city and same_state) or not ((same_first or middle_as_first) and (same_last or middle_as_last)):
                msg = "{:{ocl}d}) Do you want to keep {full_name} of {city}, {state}?{aka}".format(
                    i + 1,
                    ocl=len(str(original_count)),
                    full_name=r[1].get('name', r[0]),
                    city=address['addressLocality'],
                    state=address['addressRegion'],
                    aka=' (aka {aka})'.format(aka=aka) if len(aka) > 0 else '')
                try:
                    if input(f'\t{msg}\t').lower()[0] != 'y':
                        self.df.drop(index=r[0], inplace=True)
                except IndexError:
                    self.df.drop(index=r[0], inplace=True)

            else:
                msg = "{:{ocl}d})                kept {full_name} of {city}, {state}.{aka}".format(
                    i + 1,
                    ocl=len(str(original_count)),
                    full_name=r[1].full_name,
                    city=address['addressLocality'],
                    state=address['addressRegion'],
                    aka=' (aka {aka})'.format(aka=aka) if len(aka) > 0 else '')
                print(f'\t{msg}')

        print('\t** {count} record{s} found **\n'.format(count=len(self.df.index),
                                                         s='s' if len(self.df.index) != 1 else ''))
        return True

    def check_relatives(self, people=None):
        if not self.person.check_family:
            return False
        try:
            pr = pd.DataFrame([n for d in self.df['relatedTo'] for n in d])
            pr['givenName'] = pr['name'].str.title().str.split().str[0]
            pr['familyName'] = pr['name'].str.title().str.split().str[-1]
            pr['additionalName'] = pr['name'].str.title().str.split().str[1:-1]
        except KeyError:
            return False

        if len(pr.index) == 0:
            return False

        if people is not None:
            pr = pr[~((pr.givenName.isin(people.givenName)) & (pr.last_name.isin(people.familyName)))]

        if len(pr.index) == 0:
            return False

        orc = len(pr)
        print(f'\t** Check Relatives ({orc}) **')
        for i, r in enumerate(pr.iterrows()):

            try:
                msg = '{:{orc}d}) Would you like to add {first_name}{middle_name} {last_name}'.format(
                    i + 1,
                    orc=len(str(orc)),
                    first_name=r[1].givenName,
                    middle_name=' ' + ' '.join(r[1].additionalName) if len(r[1].additionalName) > 0 else '',
                    last_name=r[1].familyName
                )
                if input(f'\t{msg}?\t').lower()[0] == 'y':
                    self._add_relative(r[1])
            except IndexError:
                pass
        print('\t** {count} relative{s} found **\n'.format(count=len(self.relatives),
                                                           s='s' if len(self.relatives) != 1 else ''))
        return True

    def get_data(self):
        raise NoSuchMethod(f'"{self.site}" does not have function "get_data"')

    def get_soup(self):
        raise NoSuchMethod(f'"{self.site}" does not have function "get_soup"')


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


