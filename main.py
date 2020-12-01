
import pandas as pd

from collectors import COLLECTORS
from definitions import PEOPLE, NAMES_DIR


def collect_people_data(people: pd.DataFrame):
    for person in people.iterrows():
        person_id, person = person
        people = collect_person_data(person, people, person_id)
        # break

    people.to_csv(NAMES_DIR)

    return people


def collect_person_data(person: pd.Series, people: pd.DataFrame = None, person_id=None):
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
            c.check_relatives(people)
            relatives = c.relatives
            if person_id is not None:
                people.at[person_id] = c.person

        people = people.append(relatives, ignore_index=True, sort=False)
        # break
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

    people = collect_person_data(person=person)
    return True


def main():
    people = collect_people_data(PEOPLE)


if __name__ == '__main__':
    main()
    # run_check()
