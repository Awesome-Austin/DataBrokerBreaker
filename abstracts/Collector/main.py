from os import path, makedirs
import logging

import requests
import pandas as pd
from selenium.webdriver import Chrome as Driver
# from selenium.webdriver import Firefox as Driver
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup as bs

from abstracts.Collector.errors import CollectrErrors, NoRecords, NoSuchMethod, SiteSchemaChange

from definitions import OUTPUT_DIR, STATES

logging.basicConfig(level=logging.INFO, format='%(asctime)s -  %(levelname)s -  %(message)s')


class AbstractCollector:
    """Bottom Level Collectr Class"""

    def __init__(self, person, base_url, **kwargs):
        """
        :param person: Pandas.Series representing a person
        :param base_url: str for the base url for the Data Broker being scraped. ex: www.spokeo.com; www.whitepages.com
        """
        self.site = type(self).__name__
        self.person = person
        self.base_url = base_url
        self.url = None
        self.soup = None
        self.data_from_website = pd.DataFrame()
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
        if len(self.data_from_website.index) > 0:
            self.save_csv()

    def _raise_site_schema_change(self):
        """Raises an error notifing the user that the site schema changed and the source code may need update."""
        raise SiteSchemaChange(f"{self.site} has changed it schema. An update to the source code may be required.")

    def _add_relative(self, relative):
        """
        takes a series, prompts user for missing data, and appends to the current Dataframe of known relatives

        :param relative: Pandas.Series
        """
        if relative.get(key='state', default='') == '':
            relative['state'] = input('\t\tPlease enter state: (optional) ').strip().title()

        if relative.get(key='city', default='') == '':
            relative['city'] = input('\t\tPlease enter City: (optional) ').strip().title()

        if relative.get(key='middle_name', default='') == '':
            relative['middle_name'] = input('\t\tPlease enter middle name: (optional) ').strip().title()

        try:
            relative['check_family'] = bool(input('\t\tCheck relatives?: (optional) [y/n] ').lower()[0] == 'y')
        except IndexError:
            relative['check_family'] = False

        self.relatives = self.relatives.append(relative, ignore_index=True)

    def matching_relatives(self, people=None):
        """
        Cleans the 'relatedTo' field.
        Asks user if the relative should be added to the list of relatives.
        Checks if relative is already int 'people' DataFrame.
        Adds relative to DataFrame of relatives.

        :param  people : DataFrame of all the people being collected.
        :return Boolean: Next step is back where this method was called where it should have code that adds the
                         self.relatives object to the People DataFrame.
        """
        if not self.person.check_family:
            return False

        try:
            relatives = pd.DataFrame([n for d in self.data_from_website['relatedTo'] for n in d])
            relatives['first_name'] = relatives['name'].str.title().str.split().str[0]
            relatives['last_name'] = relatives['name'].str.title().str.split().str[-1]
            relatives['middle_name'] = relatives['name'].str.title().str.split().str[1:-1]
        except KeyError:
            return False

        if len(relatives.index) == 0:
            return False

        # Filter out relatives that are already in the people DataFrame
        if people is not None:
            relatives = relatives[~((relatives.first_name.isin(people.first_name)) & (relatives.last_name.isin(people.last_name)))]

        if len(relatives.index) == 0:
            return False

        orc = len(relatives)

        print(f'\t** Check Relatives ({orc}) **')
        for i, possible_relative in enumerate(relatives.iterrows()):
            row_index, possible_relative = possible_relative
            try:
                msg = '{:{orc}d}) Would you like to add {first_name}{middle_name} {last_name}? [y/n] '.format(
                    i + 1,
                    orc=len(str(orc)),
                    first_name=possible_relative.first_name,
                    middle_name=' ' + ' '.join(possible_relative.middle_name) if len(possible_relative.middle_name) > 0 else '',
                    last_name=possible_relative.last_name
                )
                if input(f'\t{msg}?\t').lower()[0] == 'y':
                    self._add_relative(possible_relative)

            except IndexError:
                pass
        print('\t** {count} relative{s} found **\n'.format(count=len(self.relatives),
                                                           s='s' if len(self.relatives) != 1 else ''))
        return True

    def save_csv(self):
        """
        Checks if self.save_dir exists, creates it if it doesn't exist.
        Saves a csv file in directory save_dir.

        :return Boolean:
        """
        if not path.exists(self.save_dir):
            makedirs(self.save_dir)
        file_name = f'{self.site}.csv'

        self.data_from_website.to_csv(path.join(self.save_dir, file_name))
        return True

    def download_file(self, url, output_file_name):
        """
        Attempts to download file to the output directory.

        :param url             : The URL for the file being downloaded.
        :param output_file_name: Where the file will be placed within the filesystem.
        :return                : boolean
        """

        output_file_dir = path.join(self.save_dir, self.site)

        # Checks if the output directory exists and creates it if it doesn't.
        if not path.exists(output_file_dir):
            makedirs(output_file_dir)

        # get info on the file being downloaded
        try:
            res = requests.get(url, allow_redirects=True, stream=True)
            res.raise_for_status()
        except Exception as e:
            logging.critical(e)
            return False

        # Generate file name with the correct extension
        output_file_name += f".{res.headers['content-type'].split('/')[1]}"

        # Download as binary
        with open(path.join(output_file_dir, output_file_name), 'wb') as f:
            for block in res.iter_content(1024):
                if not block:
                    break
                f.write(block)
        return True

    def validate_data(self):
        """
        Loops through all website records and checks if the name in the record matches the search criteria.
        If the record doesn't reasonably match it will ask the user if the record should be included in the data
            output.

        :return Boolean:
        """

        if len(self.data_from_website.index) == 0:
            return False

        original_count = len(self.data_from_website.index)

        print(f'\t** Validate Records ({original_count}) **')
        for i, website_record in enumerate(self.data_from_website.iterrows()):
            spokeo_id, website_record = website_record
            top_city_index = website_record.top_city_states_best_match_index

            if top_city_index is None:
                top_city_index = 0

            website_main_city = website_record.top_city_states[top_city_index]

            try:
                same_state = (
                        (website_main_city.get('state', '').lower() == self.person.state.lower()) or
                        (website_main_city.get('state', '').lower() == STATES.get(self.person.state.upper(), '').lower()) or
                        (STATES.get(website_main_city.get('state', '').upper(), '').lower() == self.person.state.lower()))
                same_city = website_main_city.get('city', '').lower() == self.person.city.lower()
                same_city_state = same_city and same_state

            except AttributeError:
                same_city_state = False

            website_main_name = website_record['main_name']

            same_first = self.person.first_name.lower() == website_main_name['first_name'].lower()
            same_last = self.person.last_name.lower() == website_main_name['last_name'].lower()

            try:
                middle_as_first = self.person.middle_name.lower() == website_main_name['first_name'].lower()
                middle_as_last = self.person.middle_name.lower() == website_main_name['last_name'].lower()
            except AttributeError:
                middle_as_first = False
                middle_as_last = False

            aka = '; '.join(website_record.addl_full_names)

            """
            Check if the record is in the same city and has the same first name and last name as the search.
            Sometimes the data brokers will have the middle name listed as the first name or the last name, so we
            need to control for that as well
            """

            if not same_city_state or not ((same_first or middle_as_first) and (same_last or middle_as_last)):
                msg = "{:{ocl}d}) Do you want to keep {full_name} of {city}, {state}?{aka}".format(
                    i + 1,
                    ocl=len(str(original_count)),
                    full_name=website_record.full_name,
                    city=website_main_city['city'],
                    state=website_main_city['state'],
                    aka=f' (aka {aka})' if len(aka) > 0 else '')
                try:
                    if input(f'\t{msg}\t').lower()[0] != 'y':
                        self.data_from_website.drop(index=spokeo_id, inplace=True)
                except IndexError:
                    self.data_from_website.drop(index=spokeo_id, inplace=True)

            else:
                # The extra spacing here is so that full_name here lines up with full_name
                msg = "{:{ocl}d})                kept {full_name} of {city}, {state}.{aka}".format(
                    i + 1,
                    ocl=len(str(original_count)),
                    full_name=website_record.full_name,
                    city=website_main_city['city'],
                    state=website_main_city['state'],
                    aka=' (aka {aka})'.format(aka=aka) if len(aka) > 0 else '')
                print(f'\t{msg}')

        print('\t** {count} record{s} found **\n'.format(count=len(self.data_from_website.index),
                                                         s='s' if len(self.data_from_website.index) != 1 else ''))
        return True

    def get_data(self):
        """
            Series fields required for data passed through one of the collectrs:
                first_name    -> str: 'Bruce"
                last_name     -> str: 'Wayne'
                full_name     -> str: 'Bruce Wayne'
                city          -> list if dicts:   [{city:'Gotham', state:'NY'}]
                aka           -> list of full names as str:     ['Dark Knight']
                relatedTo     -> list of full names as str:     ['Alfred Pennyworth', 'Damian Wayne']
            DataFrame can have more than this, but these are required for validate_data() and check_relatives()
            """
        raise NoSuchMethod(f'"{self.site}" does not have function "get_data"')


class RequestCollector(AbstractCollector):
    """AbstracCollectr SubClass that uses Request and BeautifySoup to collect data from site."""
    def __init__(self, person, base_url, **kwargs):
        super(RequestCollector, self).__init__(person, base_url, **kwargs)
        self.soup = None

    def __enter__(self):
        super(RequestCollector, self).__enter__()
        self.soup = self.get_soup()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(RequestCollector, self).__exit__(exc_type, exc_val, exc_tb)

    def get_soup(self):
        """
        Use the request module to get the site code and then runs it through BeautifySoup html parser.

        :return BeautifySoup:
        """
        with requests.get(self.url, headers={'User-Agent': 'Mozilla/5.0'}) as request:
            try:
                request.raise_for_status()
            except HTTPError as e:
                if '404 Client Error' in e.args[0]:
                    raise NoRecords(e.args[0])
                else:
                    raise e
            return bs(request.text, 'html.parser')


class SeleniumCollector(AbstractCollector):
    def __init__(self, person, base_url, **kwargs):
        super(SeleniumCollector, self).__init__(person, base_url, **kwargs)
        self.driver = Driver

    def __enter__(self):
        super(SeleniumCollector, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(SeleniumCollector, self).__exit__(exc_type, exc_val, exc_tb)


