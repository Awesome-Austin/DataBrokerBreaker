import csv
from os import chdir
from os.path import dirname, join, abspath

STATES = {
    'AL': 'ALABAMA',
    'AK': 'ALASKA',
    'AZ': 'ARIZONA',
    'AR': 'ARKANSAS',
    'CA': 'CALIFORNIA',
    'CO': 'COLORADO',
    'CT': 'CONNECTICUT',
    'DE': 'DELAWARE',
    'FL': 'FLORIDA',
    'GA': 'GEORGIA',
    'HI': 'HAWAII',
    'ID': 'IDAHO',
    'IL': 'ILLINOIS',
    'IN': 'INDIANA',
    'IA': 'IOWA',
    'KS': 'KANSAS',
    'KY': 'KENTUCKY',
    'LA': 'LOUISIANA',
    'ME': 'MAINE',
    'MD': 'MARYLAND',
    'MA': 'MASSACHUSETTS',
    'MI': 'MICHIGAN',
    'MN': 'MINNESOTA',
    'MS': 'MISSISSIPPI',
    'MO': 'MISSOURI',
    'MT': 'MONTANA',
    'NE': 'NEBRASKA',
    'NV': 'NEVADA',
    'NH': 'NEW HAMPSHIRE',
    'NJ': 'NEW JERSEY',
    'NM': 'NEW MEXICO',
    'NY': 'NEW YORK',
    'NC': 'NORTH CAROLINA',
    'ND': 'NORTH DAKOTA',
    'OH': 'OHIO',
    'OK': 'OKLAHOMA',
    'OR': 'OREGON',
    'PA': 'PENNSYLVANIA',
    'RI': 'RHODE ISLAND',
    'SC': 'SOUTH CAROLINA',
    'SD': 'SOUTH DAKOTA',
    'TN': 'TENNESSEE',
    'TX': 'TEXAS',
    'UT': 'UTAH',
    'VT': 'VERMONT',
    'VA': 'VIRGINIA',
    'WA': 'WASHINGTON',
    'WV': 'WEST VIRGINIA',
    'WI': 'WISCONSIN',
    'WY': 'WYOMING',
    'GU': 'GUAM',
    'PR': 'PUERTO RICO',
    'VI': 'VIRGIN ISLANDS'
}

class Person(object):
    """
    A person object to be used when scrapping / removing data.
    """
    def __init__(self, first, last, middle='', city='', state=''):
        self.first = first.title()
        self.middle = middle.title()
        self.last = last.title()
        self.city = city.title()
        if state.upper() in STATES.keys():
            state = STATES[state.upper()]
        self.state = state.title()
        self.json_file = f'../json/{self.full_name().replace(" ", "_")}.json'

    def __repr__(self):
        return str({
            'first': self.first,
            'middle': self.middle,
            'last': self.last,
            'city': self.city,
            'state': self.state
        })

    def __str__(self):
        return self.full_name().title()

    def csv_output(self):
        return [self.first, self.middle, self.last, self.city, self.state]

    def full_name(self):
        return ' '.join([self.first, self.middle, self.last]).replace('  ', ' ')

    def first_last(self):
        return ' '.join([self.first, self.last]).replace('  ', ' ')


class People(object):
    def __init__(self, csv_dir):
        self.csv_dir = csv_dir
        self.people = None
        self._people = None
        self.finished = list()
        self.not_finished = list()

    def __enter__(self):
        self.pull_people()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.output_people()
        return True

    def __str__(self):
        return '; '.join([str(p) for p in self.people])

    def __repr__(self):
        return '; '.join([repr(p) for p in self.people])

    def pull_people(self):
        with open(self.csv_dir, encoding='utf-8-sig', newline='') as cvs_file:
            reader = csv.reader(cvs_file, delimiter=',', quotechar='|')
            next(reader)
            self.people = [Person(first=p[0], middle=p[1], last=p[2], city=p[3], state=p[4]) for p in [row for row in reader]]
        return True

    def output_people(self):
        if self._people is None:
            self._people = self.people

        with open(self.csv_dir, 'w', encoding='utf-8-sig', newline='') as cvs_file:
            writer = csv.writer(cvs_file, delimiter=',', quotechar='|')
            writer.writerow('first,middle,last,city,state'.split(','))
            for person in self._people:
                writer.writerow(person.csv_output())
        return True

    def add_person(self, p: Person):
        self.people.append(p)
        return True


if __name__ == '__main__':
    with People('names.csv') as ppl:
        print(ppl)
        print(repr(ppl))
