
import pandas as pd

from collectr import COLLECTRS
from definitions import PEOPLE, NAMES_DIR


def check_people(people):
    """

    :param people:
    :return:
    """
    i = 0
    while i < len(people.index):
        person = people.iloc[i]
        people = check_person(person, people)
        i += 1
        print()
    return people


def check_person(person, people=pd.DataFrame()):
    """

    :param person:
    :param people:
    :return:
    """
    print(f'== {person.first_name} {person.last_name} ==')

    for collectr in COLLECTRS:
        while True:
            try:
                with collectr(person) as c:
                    c.validate_data()
                    c.matching_relatives(people)
                    relatives = c.relatives
                break
            except Exception as e:
                raise e
        people = people.append(relatives, ignore_index=True, sort=False)
    return people


def run_check(**kwargs):
    def _input(msg, required=True):
        while True:
            print()
            s = input(f'{msg}: (\'!\' to quit)\t')
            if s == '!':
                return False
            if (required and len(s) > 0) or not required:
                return s
            print('Please make a valid entry')

    first_name = kwargs.get('first_name')
    if first_name is None:
        first_name = _input('First Name')
    if first_name is False:
        return first_name

    last_name = kwargs.get('last_name')
    if last_name is None:
        last_name = _input('Last Name')
    if last_name is False:
        return last_name

    city = kwargs.get('city')
    if city is None:
        city = _input('City')
    if city is False:
        return city

    state = kwargs.get('state')
    if state is None:
        state = _input('State')
    if state is False:
        return state

    check_person(pd.Series({
        'first_name': first_name,
        'middle_name': '',
        'last_name': last_name,
        'city': city,
        'state': state,
        'check_family':False
    }))


def main():
    people = PEOPLE
    people = check_people(people)
    people.to_csv(NAMES_DIR)


if __name__ == '__main__':
    main()
