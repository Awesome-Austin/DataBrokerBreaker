from time import sleep
from random import randint

import pyautogui
from removr._abstract import AbstractRemover
from names import Person


class Spokeo(AbstractRemover):
    def __init__(self, email):
        super().__init__('https://www.spokeo.com/{first}-{last}/{state}', 'https://www.spokeo.com/optout', email)

    def search(self):
        self.get_json_data()

        self.driver.get(self.search_url.format(first=self.person.first, last=self.person.last, state=self.person.state))
        matches = self.driver.find_elements_by_class_name('single-column-list-item')

        for match in matches:
            # if input(f'{match.text}\nDo you want to remove this record?\n').lower()[0] == 'y':
            self.opt_out_list.add(match.get_attribute('href'))

        self.set_json_data()
        return True

    def opt_out(self, url):
        self.driver.get(self.opt_out_url)
        self.driver.find_element_by_name('url').send_keys(url)
        self.driver.find_element_by_name('email').send_keys(self.email)

        iframe = self.driver.find_elements_by_tag_name("iframe")[0]
        with open('reCAPTCHA.png', 'wb') as f:
            f.write(bytes(iframe.screenshot_as_png))
        sleep(1)
        captcha_loc = pyautogui.locateOnScreen('reCAPTCHA.png')
        l, t, w, h = captcha_loc
        pyautogui.moveTo(x=randint(l, l + w), y=randint(t, t + h), duration=2)
        pyautogui.click()
        sleep(3)
        return True
