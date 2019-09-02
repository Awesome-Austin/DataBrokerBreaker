import json
from names import Person


class AbstractCollector:
    def __init__(self, p: Person):
        self.person = p
        self.site = type(self).__name__
        self.json_data = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.json_data is not None:
            self.output_json()

    def output_json(self):
        try:
            with open(self.person.json_file, 'r') as f:
                records = dict(json.load(f))
        except FileNotFoundError:
            records = dict()

        records.setdefault(self.site, list())

        records[self.site] += self.json_data

        with open(self.person.json_file, 'w') as f:
            json.dump(records, f)
