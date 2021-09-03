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

from collectors.errors import SiteSchemaChange, NoRecords, NoSuchMethod

from definitions import OUTPUT_DIR, STATES, CHROME_DRIVER_DIR as DRIVER_DIR

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s -  %(levelname)s -  %(message)s')
logging.disable(logging.CRITICAL)

# constants used for deciding if a search record matches the Person for who we are searching.
MISMATCH_NAME = 0
MISMATCH_LOCALITY = 1
MATCH_AKA = 2
MATCH_PERSON = 3


class AbstractCollector:
    """Base Level Collector Class"""

    def __init__(self, person, base_url, **kwargs):
        """
        :param person: Pandas.Series representing a person
        :param base_url: str for the base url for the Data Broker being scraped. ex: www.spokeo.com; www.whitepages.com
        """
        self.site = type(self).__name__
        self.person = person.copy(deep=True)
        self.base_url = base_url
        self.url = None
        self.soup = None
        self.data_from_website = pd.DataFrame()
        self.relatives = pd.DataFrame()
        self.test = kwargs.get('test', False)

        ignore_people = self.person.get('ignore', '{}')
        if type(ignore_people) is str:
            ignore_people = json.loads(ignore_people.replace("'", '"'))

        self.ignore_people = ignore_people

        for k, v in kwargs.items():
            self.__setattr__(k, v)

        self.save_dir = path.join(OUTPUT_DIR, '{test}{family_name}_{given_name}'.format(
            given_name=self.person.givenName,
            family_name=self.person.familyName,
            test='__test__' if self.test else ''
        ))

    def __enter__(self):
        print(f'-- {self.site} --')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if len(self.data_from_website.index) > 0:
            self.save_csv()

    def _raise_site_schema_change(self):
        """Raises an error notifying the user that the site schema changed and the source code may need update."""
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
            * Asks user if the relative should be added to the list of relatives.
            * Checks if relative is already int 'people' DataFrame.
            * Adds relative to DataFrame of relatives.

        :param  people : DataFrame of all the people being collected.
        :return: Boolean
        """
        if not self.person.get('checkRelatives', False):
            return False

        possible_relatives = self.data_from_website.get('relatedTo', pd.Series())
        possible_relatives = [_ for _ in possible_relatives if type(_) is list]
        possible_relatives = [n for d in possible_relatives for n in d]
        possible_relatives = pd.DataFrame(possible_relatives)
        if len(possible_relatives) == 0:
            return False

        non_relatives = self.ignore_people.get('relatives', list())
        if len(non_relatives) > 0:
            possible_relatives = possible_relatives[~(possible_relatives.name.isin(pd.DataFrame(non_relatives).name))]

        if len(possible_relatives) == 0:
            return False

        split_name = possible_relatives['name'].str.title().str.split()
        possible_relatives['givenName'] = split_name.str[0]
        possible_relatives['familyName'] = split_name.str[-1]
        possible_relatives['middleName'] = split_name.str[1:-1].str.join(' ')

        if people is not None:
            possible_relatives = possible_relatives[
                ~((possible_relatives['givenName'].isin(people['givenName'])) &
                  (possible_relatives['familyName'].isin(people['familyName'])))
            ]

        if len(possible_relatives.index) == 0:
            return False

        starting_count = len(possible_relatives)

        print(f'\t** Check Relatives ({starting_count}) **')
        orc = len(str(starting_count))
        for i, possible_relative in enumerate(possible_relatives.iterrows()):
            row_index, possible_relative = possible_relative

            given_name = possible_relative.get('givenName', '').strip()

            middle_name = possible_relative.get('middleName', '')
            if type(middle_name) is list:
                middle_name = ' '.join(middle_name)
            if len(middle_name) > 0:
                middle_name = ' ' + middle_name.strip()

            family_name = possible_relative.get('familyName', '').strip()

            msg = f'{i + 1:{orc}d}) Would you like to add {given_name}{middle_name} {family_name}? [y|n] '

            try:
                add_relative = input(f'\t{msg}?\t').lower()[0] == 'y'
            except IndexError:
                add_relative = False

            if add_relative:
                self._add_relative(possible_relative)
            else:
                non_relatives.append({'name': possible_relative['name']})
                # self.person['nonRelatives'].append({'name': possible_relative['name']})

        if len(non_relatives) > 0:
            try:
                self.ignore_people['relatives'] += non_relatives
            except KeyError:
                self.ignore_people['relatives'] = non_relatives

            self.person['ignore'] = self.ignore_people

        print('\t** {count} relative{s} found **\n'.format(
            count=len(self.relatives),
            s='s' if len(self.relatives) != 1 else '')
        )

        return self.relatives

    def save_csv(self):
        """
        Saves a csv file in directory save_dir. Checks if self.save_dir exists, creates it if it doesn't exist.
        """
        if not path.exists(self.save_dir):
            makedirs(self.save_dir)
        file_name = f'{self.site}_{datetime.now().strftime("%Y-%m-%d")}.csv'

        self.data_from_website.to_csv(path.join(self.save_dir, file_name))

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
        Check if the website record is **reasonably** close to the searched person.
            * Check if the site Region (State) is the same as the person's Region.
            * Check if the Locality (City) is the same as the person's Locality.
            * Check if the record has the same first name and last name as the search.
                * Sometimes the data brokers will have the middle name listed as the first or the last name

        :param site_record: Pandas.Series representing the site record
        :return: Integer. Will be MISMATCH_NAME (0), MISMATCH_LOCALITY (1), MATCH_AKA = 2, or MATCH_PERSON (3)
        """

        def _name_perms(_first: str = '', _middle: str = '', _last: str = ''):
            """
            Generate a list of possible name variants that the DataBrokers may have
            :param _first:
            :param _middle:
            :param _last:
            :return: list() of str()
            """

            #  All plain combos of first and last name
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

            # All combos with a truncated first name
            for i in range(len(_first)):
                _names.append(f'{_first[:i]} {_last}')
                _names.append(f'{_last} {_first[:i]}')

            # All combos with a truncated last name
            for i in range(len(_last)):
                _names.append(f'{_first} {_last[:i]}')
                _names.append(f'{_last[:i]} {_first}')

            # All combos with a truncated middle name
            for i in range(len(_middle)):
                _names.append(f'{_first} {_middle[:i]}')
                _names.append(f'{_middle[:i]} {_first}')
                _names.append(f'{_first} {_middle[:i]} {_last}',)

            return _names

        # Get the most recent address on the site
        site_address = site_record.get('address', dict())

        # if the DataBroker returns a list of addresses, grab the first address on the list
        if type(site_address) is list:
            site_address = site_address[0]

        # Check the Region (state)
        site_region = site_address.get('addressRegion', '').lower()
        person_region = self.person.get('addressRegion', '').lower()
        same_region = any([
            site_region == person_region,
            site_region == STATES.get(person_region.upper(), '').lower(),
            STATES.get(site_region.upper(), '').lower() == person_region,
            ])

        # Check the Locality (city)
        site_locality = site_address.get('addressLocality', '').lower()
        person_locality = self.person.get('addressLocality', '').lower()
        same_locality = site_locality == person_locality

        same_region_and_locality = all([same_locality, same_region])

        # Get the name permutations for the search person's name.
        person_aka = _name_perms(
            _first=self.person['givenName'].lower(),
            _middle=self.person['middleName'].lower(),
            _last=self.person['familyName'].lower()
        )

        # Get the name permutations for the site record's name.
        site_record_name = site_record['name'].lower()
        _site_record_name = site_record_name.split(' ')
        site_aka = _name_perms(
            _first=_site_record_name[0],
            _middle=''.join(_site_record_name[1:-1]),
            _last=_site_record_name[-1]
        )

        # Check if the Site Record name is in the generate list of the Search Person's A.K.A.s
        if site_record_name not in person_aka:
            matches_aka = [aka in person_aka for aka in site_aka]
            if not any(matches_aka):  # If none of the possible name variants match
                logging.debug(f'MISMATCH_NAME: {site_record_name}')
                return MISMATCH_NAME
            else:
                logging.debug(f'MATCH_AKA: {site_record_name}')
                return MATCH_AKA

        if not same_region_and_locality:
            logging.debug(f'MISMATCH_LOCALITY: {site_record_name}')
            return MISMATCH_LOCALITY

        logging.debug(f'MATCH_PERSON: {site_record_name}')
        return MATCH_PERSON

    def validate_data(self):
        """
        Loops through all website records and checks if the name in the record matches the search criteria.
        If the record doesn't reasonably match it will ask the user if the record should be included in the data
            output.

        :return: Boolean
        """

        original_count = len(self.data_from_website.index)
        print(f'\t** Validate Records ({original_count}) **')
        if original_count == 0:
            return self.person

        possible_matches = self.data_from_website.copy(deep=True)

        non_matches = self.ignore_people.get('searchResults', dict())
        if len(non_matches) > 0:
            possible_matches = possible_matches[~(
                possible_matches.index.isin(pd.DataFrame(index=non_matches.get(self.site.lower(), list())).index)
            )]

        if len(possible_matches) == 0:
            return self.person

        for i, site_record in enumerate(possible_matches.iterrows()):
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

            # Get the list of matches confirmed by previous user run to not be a true match
            if site_record_check == MISMATCH_LOCALITY or site_record_check == MATCH_AKA:
                try:
                    remove_site_id = input(f'\t{msg}\t').lower()[0] != 'y'
                except IndexError:
                    remove_site_id = True
            else:
                print(f'\t{msg}')
                remove_site_id = (site_record_check == MISMATCH_NAME)

            if remove_site_id:
                try:
                    non_matches[self.site.lower()].append(site_id)
                    # self.person['nonMatch'][self.site.lower()].append(site_id)
                except KeyError:
                    non_matches[self.site.lower()] = [site_id]
                    # self.person['nonMatch'][self.site.lower()] = [site_id]

                self.data_from_website.drop(index=site_id, inplace=True)

        if len(non_matches) > 0:
            try:
                self.ignore_people['searchResults'].update(non_matches)
            except KeyError:
                self.ignore_people['searchResults'] = non_matches

            self.person['ignore'] = self.ignore_people

        print('\t** {count} record{s} found **\n'.format(
            count=len(self.data_from_website.index),
            s='s' if len(self.data_from_website.index) != 1 else ''))
        return self.person

    def get_data(self):
        """This method needs to be superseded by the Specific Collector Subclass."""
        raise NoSuchMethod(f"self.get_data has not been created for {self.site} Collector")


class RequestCollector(AbstractCollector):
    """AbstractCollector SubClass that uses Request and BeautifySoup to collect data from site."""
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

        :return: BeautifySoup
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
        the data off the site. This class will use a browser (Firefox or Chrome). The browser choice is selected in
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
