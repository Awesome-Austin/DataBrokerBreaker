import os
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(ROOT_DIR, 'tests')
FILES_DIR = os.path.join(ROOT_DIR, 'files')
OUTPUT_DIR = os.path.join(FILES_DIR, 'output')
NAMES_DIR = os.path.join(FILES_DIR, 'names.csv')
DRIVERS_DIR = os.path.join(ROOT_DIR, 'drivers', )

PEOPLE = pd.read_csv(NAMES_DIR, index_col=0)

CHROME_DRIVER_DIR = os.path.join(DRIVERS_DIR, 'chromedriver.exe')
# FIREFOX_DRIVER_DIR = os.path.join(DRIVERS_DIR, '')

SCROLL_PAUSE_TIME = 1.5

with open(os.path.join(FILES_DIR, 'email.txt')) as f:
    EMAIL = f.readlines()[0].strip()

STATES = {'AL': 'ALABAMA', 'AK': 'ALASKA', 'AZ': 'ARIZONA', 'AR': 'ARKANSAS', 'CA': 'CALIFORNIA', 'CO': 'COLORADO',
          'CT': 'CONNECTICUT', 'DE': 'DELAWARE', 'FL': 'FLORIDA', 'GA': 'GEORGIA', 'HI': 'HAWAII', 'ID': 'IDAHO',
          'IL': 'ILLINOIS', 'IN': 'INDIANA', 'IA': 'IOWA', 'KS': 'KANSAS', 'KY': 'KENTUCKY', 'LA': 'LOUISIANA',
          'ME': 'MAINE', 'MD': 'MARYLAND', 'MA': 'MASSACHUSETTS', 'MI': 'MICHIGAN', 'MN': 'MINNESOTA',
          'MS': 'MISSISSIPPI', 'MO': 'MISSOURI', 'MT': 'MONTANA', 'NE': 'NEBRASKA', 'NV': 'NEVADA',
          'NH': 'NEW HAMPSHIRE', 'NJ': 'NEW JERSEY', 'NM': 'NEW MEXICO', 'NY': 'NEW YORK', 'NC': 'NORTH CAROLINA',
          'ND': 'NORTH DAKOTA', 'OH': 'OHIO', 'OK': 'OKLAHOMA', 'OR': 'OREGON', 'PA': 'PENNSYLVANIA',
          'RI': 'RHODE ISLAND', 'SC': 'SOUTH CAROLINA', 'SD': 'SOUTH DAKOTA', 'TN': 'TENNESSEE', 'TX': 'TEXAS',
          'UT': 'UTAH', 'VT': 'VERMONT', 'VA': 'VIRGINIA', 'WA': 'WASHINGTON', 'WV': 'WEST VIRGINIA', 'WI': 'WISCONSIN',
          'WY': 'WYOMING', 'GU': 'GUAM', 'PR': 'PUERTO RICO', 'VI': 'VIRGIN ISLANDS'}

TEST_PERSON = pd.Series(
    {'first_name': 'John',
     'last_name': 'Smith',
     'city': 'Los Angeles',
     'state': 'Ca',
     'check_family': False}
)
