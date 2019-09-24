import requests
import json
from time import sleep
from bs4 import BeautifulSoup as bs
from urllib.parse import urljoin
import pandas as pd


from collectr._abstract import RequestCollectr, SeleniumCollectr
from definitions import TEST_PERSON

BASE_URL = 'https://www.whitepages.com/'


class WhitePages(SeleniumCollectr):
    def __init__(self, person, **kwargs):
        super(WhitePages, self).__init__(person, BASE_URL, **kwargs)
        self.url = urljoin(self.base_url, '/name/{givenName}-{familyName}{addressRegion}{addressLocality}'.format(
            givenName=self.person.givenName,
            familyName=self.person.familyName,
            addressRegion="/" + self.person.get('addressRegion') if len(
                self.person.get('addressRegion', '')) > 0 else '',
            addressLocality="/" + self.person.get('addressLocality') if len(
                self.person.get('addressLocality', '')) > 0 else ''
        ))

    def __enter__(self):
        super(WhitePages, self).__enter__()
        self.get_data()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(WhitePages, self).__exit__(exc_type, exc_val, exc_tb)

    def get_data(self):
        with self.driver() as driver:
            driver.get(self.url)
            while True:
                txt = driver.page_source
                soup = bs(txt, 'html.parser')
                captcha_on_page = soup.find("div", {'class': 'captcha-wrapper'}) is not None
                robo_caught = soup.find('meta', {'name': "ROBOTS"}) is not None
                if not captcha_on_page and not robo_caught:
                    break

        df = pd.DataFrame([json.loads(r.strip().replace('//<![CDATA[\n', '').replace('\n//]]>', '')) for r in
                           [r.text.strip() for r in soup.find_all(type='application/ld+json')] if
                           '"@type":"Person"' in r])
        df['id'] = df['URL'].str.split('/', expand=True)[4]
        df.set_index('id', inplace=True)
        self.df = pd.DataFrame(df)


if __name__ == '__main__':
    with WhitePages(TEST_PERSON, test=True) as wp:
        wp.validate_data()
        wp.check_relatives()
