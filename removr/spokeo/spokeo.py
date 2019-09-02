from os import chdir
from os.path import dirname
from time import sleep
from random import randint

import pyautogui
from selenium.webdriver import Chrome

pyautogui.PAUSE = 1
pyautogui.FAILSAFE = True

URL = 'https://www.spokeo.com'
chdir(dirname(__file__))


class Spokeo:
    def __init__(self, email):
        self.email = email

    def url(self, person):
        return f'{URL}/{person.first}-{person.last}/{person.state}'

    def search(self, person):
        with Chrome() as driver:
            driver.get(self.url(person))
            matches = driver.find_elements_by_class_name('single-column-list-item')
            for i, match in enumerate(matches):
                print(match.text)
                print('Do you want to remove this record?')
                if input().lower()[0] == 'y':
                    self.optout(match.get_attribute('href'))

        return True

    def opt_out(self, url):
        with Chrome() as driver:
            driver.get(f'{URL}/optout')
            driver.find_element_by_name('url').send_keys(url)
            driver.find_element_by_name('email').send_keys(self.email)

            iframe = driver.find_elements_by_tag_name("iframe")[0]
            with open('reCAPTCHA.png', 'wb') as f:
                f.write(bytes(iframe.screenshot_as_png))
            sleep(1)
            captcha_loc = pyautogui.locateOnScreen('reCAPTCHA.png')
            l, t, w, h = captcha_loc
            pyautogui.moveTo(x=randint(l, l + w), y=randint(t, t + h), duration=2)
            pyautogui.click()
            sleep(3)

        return True


if __name__ == '__main__':
    s = Spokeo('test1')
    s.opt_out('test2')

