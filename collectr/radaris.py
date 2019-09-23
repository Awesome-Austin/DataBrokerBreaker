from urllib.parse import urljoin

from collectr._abstract import SeleniumCollectr, NoRecords
from definitions import TEST_PERSON, STATES

BASE_URL = 'https://radaris.com/'


class Radaris(SeleniumCollectr):

    def __init__(self, person, **kwargs):

        super(Radaris, self).__init__(person, BASE_URL, **kwargs)
        self.person.state = STATES.get(self.person.state.upper(), self.person.state).title()
        print(self.person)
        self.url = urljoin(self.base_url, 'ng/search?{}'.format(
            '&'.join(
                [s for s in ['{}'.format(f'ff={self.person.first_name}' if self.person.first_name is not None else ''),
                             '{}'.format(f'fl={self.person.last_name}' if self.person.last_name is not None else ''),
                             '{}'.format(f'fs={self.person.state}' if self.person.state is not None else ''),
                             '{}'.format(f'fc={self.person.city}' if self.person.city is not None else '')
                             ] if len(s) > 0])))

    def __enter__(self):
        super(Radaris, self).__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(Radaris, self).__exit__(exc_type, exc_val, exc_tb)


if __name__ == '__main__':
    with Radaris(TEST_PERSON, test=True) as rad:
        print(rad.url)
