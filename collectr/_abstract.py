from os import path, makedirs

import requests
import pandas as pd
from selenium.webdriver import Chrome as Driver
# from selenium.webdriver import Firefox as Driver
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup as bs


from definitions import OUTPUT_DIR


class NoRecords(Exception): pass


class NoSuchMethod(Exception): pass


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

        self.save_dir = path.join(OUTPUT_DIR, '{test}{first_name}_{last_name}'.format(
            first_name=self.person.first_name,
            last_name=self.person.last_name,
            test='__test__' if self.test else ''
        ))

    def __enter__(self):
        print(f'-- {self.person.first_name} {self.person.last_name} --')
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

    def clean_data(self):
        raise NoSuchMethod(f'"{self.site}" does not have function "clean_data"')

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
            print(request.text)
            self.soup = bs(request.text, 'html.parser')


class SeleniumCollectr(AbstractCollectr):
    def __init__(self, person, base_url, **kwargs):
        super(SeleniumCollectr, self).__init__(person, base_url, **kwargs)

    def __enter__(self):
        super(SeleniumCollectr, self).__enter__()
        self.driver = Driver()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(SeleniumCollectr, self).__exit__(exc_type, exc_val, exc_tb)
        self.driver.close()


