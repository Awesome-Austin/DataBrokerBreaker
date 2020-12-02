from os import path, makedirs
import logging
import json
from datetime import datetime


import requests
import pandas as pd
from selenium.webdriver import Chrome as Driver
# from selenium.webdriver import Firefox as Driver
from requests.exceptions import HTTPError
from bs4 import BeautifulSoup as bs

from abstracts.Collector.errors import NoRecords, NoSuchMethod, SiteSchemaChange

from definitions import OUTPUT_DIR, STATES, CHROME_DRIVER_DIR as DRIVER_DIR

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -  %(levelname)s -  %(message)s')
logging.disable(logging.CRITICAL)

# constants used for deciding if a search record matches the Person for who we are searching.
MISMATCH_NAME = 0
MISMATCH_LOCALITY = 1
MATCH_AKA = 2
MATCH_PERSON = 3


class AbstractCollector:
    """Base Level Collectr Class"""

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

        self.save_dir = path.join(OUTPUT_DIR, '{test}{givenName}_{familyName}'.format(
            givenName=self.person.givenName,
            familyName=self.person.familyName,
            test='__test__' if self.test else ''
        ))
        self.save_dir = path.join(self.save_dir,  datetime.now().strftime("%Y-%m-%d"))

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
        # Check addressRegion (state)
        if relative.get(key='addressRegion', default='') == '':
            relative['addressRegion'] = input('\t\tPlease enter State: (optional) ').strip().title()

        # Check addressLocality (city)
        if relative.get(key='addressLocality', default='') == '':
            relative['addressLocality'] = input('\t\tPlease enter City: (optional) ').strip().title()

        if relative.get(key='middleName', default='') == '':
            relative['middleName'] = input('\t\tPlease enter middle name: (optional) ').strip().title()

        try:
            relative['checkRelatives'] = bool(input('\t\tCheck relatives?: (optional) [y/n] ').lower()[0] == 'y')
        except IndexError:
            relative['checkRelatives'] = False

        relative['givenName'] = relative['givenName'].strip().title()
        relative['familyName'] = relative['familyName'].strip().title()
        relative['middleName'] = ''.join(relative['middleName']).strip().title()
        relative['addressLocality'] = relative['addressLocality'].strip().title()
        relative['addressRegion'] = relative['addressRegion'].strip().upper()

        relative.drop(inplace=True, columns=[
            'name',
        ])

        self.relatives = self.relatives.append(relative, ignore_index=True)

    def check_relatives(self, people=None):
        """
        Cleans the 'relatedTo' field.
        Asks user if the relative should be added to the list of relatives.
        Checks if relative is already int 'people' DataFrame.
        Adds relative to DataFrame of relatives.

        :param  people : DataFrame of all the people being collected.
        :return Boolean: Next step is back where this method was called where it should have code that adds the
                         self.relatives object to the People DataFrame.
        """
        if not self.person.get('checkRelatives', False):
            return False

        possible_relatives = self.data_from_website.get('relatedTo', list())
        possible_relatives = pd.DataFrame([n for d in possible_relatives for n in d])
        if len(possible_relatives) == 0:
            return False

        # Filter out relatives that are already in the people DataFrame
        # if self.person.get("non_relatives", None) is None:
        #     self.person["non_relatives"] = list()

        if len(self.person.get("non_relatives", '')) == 0:
            self.person["non_relatives"] = list()

        else:
            if type(self.person["non_relatives"]) == str:
                self.person["non_relatives"] = json.loads(self.person["non_relatives"].replace("'", '"'))
            non_relatives = pd.DataFrame(self.person["non_relatives"])
            possible_relatives = possible_relatives[~(possible_relatives.name.isin(non_relatives.name))]
            if len(possible_relatives) == 0:
                return False

        split_name = possible_relatives['name'].str.title().str.split()
        possible_relatives['givenName'] = split_name.str[0]
        possible_relatives['familyName'] = split_name.str[-1]
        possible_relatives['middleName'] = split_name.str[1:-1].str.join(' ')

        if people is not None:
            possible_relatives = possible_relatives[
                ~((possible_relatives['givenName'].isin(people['givenName'])) & (possible_relatives['familyName'].isin(people['familyName'])))
            ]

        if len(possible_relatives.index) == 0:
            return False

        starting_count = len(possible_relatives)

        print(f'\t** Check Relatives ({starting_count}) **')
        for i, possible_relative in enumerate(possible_relatives.iterrows()):
            row_index, possible_relative = possible_relative
            # try:
            msg = '{:{orc}d}) Would you like to add {givenName}{middleName} {familyName}? [y/n] '.format(
                i + 1,
                orc=len(str(starting_count)),
                givenName=possible_relative.get('givenName', ''),
                middleName=f" {' '.join(possible_relative.get('middleName', ''))}" if (
                        len(possible_relative.get('middleName', '')) > 0) else '',
                familyName=possible_relative.get('familyName', '')
            )

            try:
                add_relative = input(f'\t{msg}?\t').lower()[0] == 'y'
            except IndexError:
                add_relative = False

            if add_relative:
                self._add_relative(possible_relative)
            else:
                self.person['non_relatives'].append({'name': possible_relative['name']})

        print('\t** {count} relative{s} found **\n'.format(
            count=len(self.relatives),
            s='s' if len(self.relatives) != 1 else '')
        )

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

    def _site_record_matches_person(self, site_record):
        """
        Check if the website record is reasonably close to the searched person.
            * Check if the site Region (State) is the same as the person's Region.
            * Check if the Locality (City) is the same as the person's Locality.
            * Check if the record is in the same city and has the same first name and last name as the search.
                * Sometimes the data brokers will have the middle name listed as the first name or the last name, so
                  we need to control for that as well.

        :param site_record: Pandas.Series representing the site record
        :return Integer: Will be MISMATCH_NAME (0), MISMATCH_LOCALITY (1), or MATCH_PERSON (2)
        """

        def _name_perms(_first: str = '', _middle: str = '', _last: str = ''):
            _names = [
                f'{_first} {_last}',
                f'{_last} {_first}',
                f'{_first} {_middle}',
                f'{_middle} {_last}',
                f'{_first} {_middle} {_last}',
                f'{_first} {_middle}-{_last}',
                f'{_first}{_middle} {_last}',
                f'{_first} {_middle}{_last}',
            ]

            for i in range(len(_first)):
                _names.append(f'{_first[:i]} {_last}')
                _names.append(f'{_last} {_first[:i]}')

            for i in range(len(_last)):
                _names.append(f'{_first} {_last[:i]}')
                _names.append(f'{_last[:i]} {_first}')

            for i in range(len(_middle)):
                _names.append(f'{_first} {_middle[:i]}')
                _names.append(f'{_middle[:i]} {_first}')
                _names.append(f'{_first} {_middle[:i]} {_last}',)

            return _names

        # Get the most recent address on the site
        site_address = site_record.get('address', dict())
        if type(site_address) is list:
            site_address = site_address[0]

        # Start with the Region (state)
        site_region = site_address.get('addressRegion', '').lower()
        person_region = self.person.get('addressRegion', '').lower()
        same_region = any([
            site_region == person_region,
            site_region == STATES.get(person_region.upper(), '').lower(),
            STATES.get(site_region.upper(), '').lower() == person_region,
            ])

        # Continue with the Locality (city)
        site_locality = site_address.get('addressLocality', '').lower()
        person_locality = self.person.get('addressLocality', '').lower()
        same_locality = site_locality == person_locality

        same_region_and_locality = all([same_locality, same_region])

        person_akas = _name_perms(
            _first=self.person['givenName'].lower(),
            _middle=self.person['middleName'].lower(),
            _last=self.person['familyName'].lower()
        )

        site_name = site_record['name'].lower()
        _site_name = site_name.split(' ')
        site_akas = _name_perms(
            _first=_site_name[0],
            _middle=''.join(_site_name[1:-1]),
            _last=_site_name[-1]
        )

        matches_aka = [aka in person_akas for aka in site_akas]

        if site_name not in person_akas:
            if not any(matches_aka):
                logging.debug(f'MISMATCH_NAME: {site_name}')
                return MISMATCH_NAME
            else:
                logging.debug(f'MATCH_AKA: {site_name}')
                return MATCH_AKA

        if not same_region_and_locality:
            logging.debug(f'MISMATCH_LOCALITY: {site_name}')
            return MISMATCH_LOCALITY

        # if not any(matches_aka):
        logging.debug(f'MATCH_PERSON: {site_name}')
        return MATCH_PERSON

    def validate_data(self):
        """
        Loops through all website records and checks if the name in the record matches the search criteria.
        If the record doesn't reasonably match it will ask the user if the record should be included in the data
            output.

        :return Boolean:
        """
        original_count = len(self.data_from_website.index)
        print(f'\t** Validate Records ({original_count}) **')
        if original_count == 0:
            return False

        for i, site_record in enumerate(self.data_from_website.iterrows()):
            site_id, site_record = site_record

            additional_names = site_record.get('additionalName', [])
            additional_names = '; '.join(additional_names[:min([len(additional_names), 3])])
            site_address = site_record.get('address', dict())
            if type(site_address) is list:
                site_address = site_address[0]

            site_record_check = self._site_record_matches_person(site_record)
            msg = {
                MISMATCH_NAME:     '{:{ocl}d})             skipped {name_} of {city}, {state}.{aka}',
                MISMATCH_LOCALITY: '{:{ocl}d}) Do you want to keep {name_} of {city}, {state}?{aka} [y|n]',
                MATCH_AKA:         '{:{ocl}d}) Do you want to keep {name_} of {city}, {state}?{aka} [y|n]',
                MATCH_PERSON:      '{:{ocl}d})                kept {name_} of {city}, {state}.{aka}',
            }[site_record_check]

            msg = msg.format(
                i + 1,
                ocl=len(str(original_count)),
                name_=site_record.get('name'),
                city=site_address.get('addressLocality', 'Unknown City'),
                state=site_address.get('addressRegion', ""),
                aka=f' (aka {additional_names})' if len(additional_names) > 0 else ''
            )

            if site_record_check == MISMATCH_LOCALITY or site_record_check == MATCH_AKA:
                try:
                    if input(f'\t{msg}\t').lower()[0] != 'y':
                        self.data_from_website.drop(index=site_id, inplace=True)
                except IndexError:
                    self.data_from_website.drop(index=site_id, inplace=True)

            else:
                print(f'\t{msg}')
                if site_record_check == MISMATCH_NAME:
                    self.data_from_website.drop(index=site_id, inplace=True)

        print('\t** {count} record{s} found **\n'.format(count=len(self.data_from_website.index),
                                                         s='s' if len(self.data_from_website.index) != 1 else ''))
        return True

    def get_data(self):
        """This method should be overridden by all subclasses."""
        raise NoSuchMethod(f'"{self.site}" does not have function "get_data"')


class RequestCollector(AbstractCollector):
    """AbstractCollectr SubClass that uses Request and BeautifySoup to collect data from site."""
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
    """
    Collector Class for DataBrokers that use Javascript, or don't use JSON.
    IF the Site uses Javascript to load data after the page has loaded then the 'request' module will not work to pull
        the data off the site. This class will use a webbrowser (Firefox or Chrome). The browser choice is selected in
        the header data of this module.
    """

    DRIVER_DIR = DRIVER_DIR

    def __init__(self, person, base_url, **kwargs):
        """
        :param person: Pandas.Series representing a person
        :param base_url: str for the base url for the Data Broker being scraped. ex: www.spokeo.com; www.whitepages.com
        """
        super(SeleniumCollector, self).__init__(person, base_url, **kwargs)
        self.driver = Driver

    def __enter__(self):
        super(SeleniumCollector, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(SeleniumCollector, self).__exit__(exc_type, exc_val, exc_tb)


