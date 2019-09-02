import requests
import re
import json
from urllib.parse import urljoin
from os import path

from bs4 import BeautifulSoup as bs

from collectr._abstract import AbstractCollector
from collectr.spokeo import SpokeoRecord
from names import Person


class NoRecords(Exception): pass


class Spokeo(AbstractCollector):
    def __init__(self, p: Person):
        super(Spokeo, self).__init__(p)
        self.re_data = re.compile('(var...PRELOADED.STATE...=.)(.*{}})')
        self.base_url = 'https://www.spokeo.com'
        self.search_url = urljoin(self.base_url, '/'.join([f'{p.first} {p.last}', p.state, p.city]).replace(' ', '-'))
        self.data = list()
        self.request = None
        self.soup = None
        self.data = None

    def __enter__(self):
        self.pull_data()
        return super(Spokeo, self).__enter__()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.data is not None:
            self.json_data = [d.raw for d in self.data]
        super(Spokeo, self).__exit__(exc_type, exc_val, exc_tb)

    def __str__(self):
        pass

    def pull_data(self):
        self.request = requests.get(urljoin(self.base_url, self.search_url))
        try:
            self.request.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if e.args[0] in f'*404 Client Error: Not Found for url: {self.search_url}*':
                raise NoRecords(e.args[0])
            else:
                raise e

        self.soup = bs(self.request.text, 'html.parser')

        for d in [d for d in self.soup.find_all('script') if len(self.re_data.findall(d.text)) > 0]:
            self.data = [SpokeoRecord(j) for j in json.loads(''.join([group[1] for group in self.re_data.findall(d.text)]))['people']]
        return True

    def validate(self):
        _data = []
        while self.data:
            d = self.data.pop()
            print(d)
            if input('Add this record?\t').lower()[0] == 'y':
                _data.append(d)
            print()
        self.data = _data


if __name__ == '__main__':
    pass