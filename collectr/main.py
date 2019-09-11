from collectr import Spokeo


def spokeo(person, people):
    with Spokeo(person) as s:
        s.validate_records()
        s.check_relatives(people)
        return people.append(s.relatives, ignore_index=True, sort=False)


def main(person, people):
    people = spokeo(person, people)
    return people
