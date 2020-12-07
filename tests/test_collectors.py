from collectors import COLLECTORS, MyLife
from tests import TEST_PERSON


def test_all():
    for collector in COLLECTORS:
        with collector(TEST_PERSON, test=True) as c:
            c.validate_data()
            if c.check_relatives():
                relatives = c.relatives
                print(relatives)


def test_mylife():
    with MyLife(TEST_PERSON, test=True) as c:
        c.validate_data()
        if c.check_relatives():
            relatives = c.relatives
            print(relatives)


if __name__ == '__main__':
    test_all()
    # test_mylife()
