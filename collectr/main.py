from collectr.spokeo import Spokeo, NoRecords
from names import Person, People


def spokeo(p: Person, check_family=False):
    try:
        with Spokeo(p) as s:
            if p.state == '' or p.city == '':
                print()
                s.validate()
                if len(s.data) == 0:
                    return
                p.state = s.data[0].top_city().state
                p.city = s.data[0].top_city().name
                print()
            family = [r for record in s.data for r in record.family_members]
            if check_family and len(family) > 0:
                for first, last in [name.split() for name in family]:
                    if input(f'\tDo you want to add "{first} {last}"?').lower()[0] == 'y':
                        ppl.add_person(Person(first=first, last=last))
                print()
    except NoRecords as e:
        print(f'\t{e.args[0]}')

    except Exception as e:
        raise e


if __name__ == '__main__':
    with People('../files/names.csv') as ppl:
        for person in ppl.people:
            print(person)
            spokeo(person)
            # break
