__author__ = 'awesome_austin'
import json

from os.path import join, dirname

from selenium.webdriver import Chrome as Driver


j_file = join(dirname(dirname(__file__)), 'urls.json')


class AbstractRemover:
    def __init__(self, search_url, opt_out_url, email, test=False):
        self.search_url = search_url
        self.opt_out_url = opt_out_url
        self.email = email
        self.person = ''
        self._json_file = '{name}.json'
        self.opt_out_list = set()

    def __enter__(self):
        self.driver = Driver()
        # try:
        #     with open(j_file, 'r') as json_file:
        #         self.opt_out_list = set(json.load(json_file)[type(self).__name__])
        # except json.decoder.JSONDecodeError:
        #     self.opt_out_list = set()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # try:
        #     with open(j_file, 'r') as json_file:
        #         full_list = json.load(json_file)
        # except json.decoder.JSONDecodeError:
        #     full_list = dict()
        #
        # full_list.setdefault(type(self).__name__, list())
        # full_list[type(self).__name__] += list(self.opt_out_list)
        #
        # with open(j_file, 'w') as json_file:
        #     json.dump(full_list, json_file)
        self.driver.close()

    def json_file(self):
        try:
            return self._json_file.format(name=self.person.full_name().replace(' ', '_'))
        except AttributeError as e:
            if type(self.person) == str:
                raise TypeError('Please enter a person.')
            else:
                raise e

    def get_json_data(self):
        try:
            with open(self.json_file(), 'r') as json_file:
                self.opt_out_list = set(json.load(json_file)[type(self).__name__])
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            self.opt_out_list = set()

    def set_json_data(self):
        try:
            with open(self.json_file(), 'r') as json_file:
                full_list = json.load(json_file)
        except FileNotFoundError:
            pass
        except json.decoder.JSONDecodeError:
            full_list = dict()

        full_list.setdefault(type(self).__name__, list())
        full_list[type(self).__name__] += list(self.opt_out_list)

        with open(j_file, 'w') as json_file:
            json.dump(full_list, json_file)
