import logging
import random
from datetime import datetime
from time import sleep
from random import randint
from os import path, remove, makedirs
from urllib.parse import urljoin

import pyautogui
import pandas as pd
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from definitions import EMAIL, FILES_DIR


logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.DEBUG)

pyautogui.PAUSE = 1
pyautogui.FAILSAFE = True

BASE_URL = 'https://www.spokeo.com'

TIMEOUT = 5  # seconds


class SpokeoRemovr:
    def __init__(self, csv_file, email=''):
        self.csv_file = csv_file
        self.df = pd.read_csv(self.csv_file, index_col=0)
        self.base_url = BASE_URL
        self.opt_out_url = urljoin(self.base_url, 'optout')
        self.email = {True: email, False: EMAIL}[email != '']
        self.output_dir = path.join(FILES_DIR, 'Removr', type(self).__name__)
        if not path.exists(self.output_dir):
            makedirs(self.output_dir)
        self._short_sleep = lambda: sleep(random.uniform(0, 1))
        self._sleep = lambda: sleep(random.uniform(0, 3))

        if 'opted_out' not in self.df.index:
            self.df['opted_out'] = False

        if 'opt_out_date' not in self.df.index:
            self.df['opt_out_date'] = ''

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.df.to_csv(self.csv_file)
        return True

    def opt_out(self):
        for i, record in self.df.iterrows():
            if record.opted_out is False:
                self._opt_out(record.url)
                self.df.loc[i, 'opted_out'] = True
                self.df.loc[i, 'opt_out_date'] = datetime.today()

    def _click_element(self, element):
        element_dir = path.join(self.output_dir, f'{element.id}.png')
        with open(element_dir, 'wb') as f:
            f.write(bytes(element.screenshot_as_png))

        self._short_sleep()
        element_loc = pyautogui.locateOnScreen(element_dir)
        remove(element_dir)

        l, t, w, h = element_loc
        pyautogui.moveTo(x=randint(l, l + w), y=randint(t, t + h), duration=random.uniform(1, 4))
        self._sleep()
        pyautogui.click()

    def _opt_out(self, url):
        with Chrome() as driver:
            driver.get(self.opt_out_url)
            re_captcha = WebDriverWait(driver, TIMEOUT).until(
                ec.presence_of_element_located(
                    (By.XPATH, "//iframe[starts-with(@src, 'https://www.google.com/recaptcha/api2/anchor?ar=')]")))

            self._short_sleep()
            textbox_url = driver.find_element_by_name('url')
            self._click_element(textbox_url)
            textbox_url.send_keys(urljoin(self.base_url, url))

            self._sleep()
            textbox_url.send_keys(Keys.TAB)

            self._sleep()
            textbox_email = driver.find_element_by_name('email')
            textbox_email.send_keys(self.email)

            self._short_sleep()
            self._click_element(re_captcha)
            self._short_sleep()
            input('press any key to continue')

        return True
