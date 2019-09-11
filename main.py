import logging

from collectr.spokeo import Spokeo
from definitions import PEOPLE, NAMES_DIR

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

i = 0
while i < len(PEOPLE.index):
    with Spokeo(PEOPLE.iloc[i]) as s:
        # s.validate_records()
        # s.check_relatives(PEOPLE)
        PEOPLE = PEOPLE.append(s.relatives, ignore_index=True, sort=False)
    i += 1

PEOPLE.to_csv(NAMES_DIR)
