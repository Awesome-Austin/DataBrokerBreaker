
import pandas as pd

from collectors import COLLECTORS
from definitions import PEOPLE, NAMES_DIR


def collect_people_data(people: pd.DataFrame):
    people = people.copy(deep=True).reset_index(drop=True)
    i = 0
    while True:
        person, people = collect_person_data(people.iloc[i], people)
        i += 1
        if i == len(people.index):
            break

    people.to_csv(NAMES_DIR)

    return people


def collect_person_data(person: pd.Series, people: pd.DataFrame = None):
    if people is None:
        people = pd.DataFrame({}, columns=[
            'givenName',
            'middleName',
            'familyName',
            'addressLocality',
            'addressRegion',
            'checkRelatives',
            'none_relatives',
        ])

    print(f'== {person.get("givenName", "___")} {person.get("familyName", "___")} ==')

    for collector in COLLECTORS:
        with collector(person) as c:
            c.validate_data()
            person = c.person.copy(deep=True)
            relatives = c.check_relatives(people)
            if relatives is False:
                continue
            people = people.append(relatives, ignore_index=True)

    if person.get('name', '') in people.index:
        people = people.drop(person.name).append(person, ignore_index=False).sort_index()
        # people.loc[person.name] = person

    return person, people


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

    given_name = kwargs.get('givenName')
    if given_name is None:
        given_name = _input('First Name')
    if given_name is False:
        return False

    middle_name = kwargs.get('middleName')
    if middle_name is None:
        middle_name = _input('Middle Name', required=False)

    family_name = kwargs.get('familyName')
    if family_name is None:
        family_name = _input('Last Name')
    if family_name is False:
        return False

    address_locality = kwargs.get('addressLocality')
    if address_locality is None:
        address_locality = _input('City')
    if address_locality is False:
        return False

    address_region = kwargs.get('addressRegion')
    if address_region is None:
        address_region = _input('State')
    if address_region is False:
        return False

    check_family = kwargs.get('checkRelatives', False)

    person = pd.Series({
        'givenName': given_name.title(),
        'middleName': middle_name.title(),
        'familyName': family_name.title(),
        'addressLocality': address_locality.title(),
        'addressRegion': address_region.title(),
        'checkRelatives': check_family,
    })

    collect_person_data(person=person)
    return True


def main():
    collect_people_data(PEOPLE)


if __name__ == '__main__':
    main()
    # run_check()
