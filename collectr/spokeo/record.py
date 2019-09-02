null = None
true = True
false = False


class SpokeoRecord:
    def __init__(self, spokeo_record):
        self.raw = spokeo_record

        self.id = spokeo_record['id']
        self.first_name = spokeo_record['main_name']['first_name']
        self.middle_name = spokeo_record['main_name']['last_name']
        self.last_name = spokeo_record['main_name']['middle_name']
        self.full_name = spokeo_record['full_name']

        self.age = spokeo_record['age']
        self.cities = [City(c) for c in spokeo_record['top_city_states']]
        self.top_city_index = spokeo_record['top_city_states_best_match_index']
        self.family_members = spokeo_record['family_members']
        self.additional_names = spokeo_record['addl_full_names']
        self.phone_count = spokeo_record['email_count']
        self.email_count = spokeo_record['phone_count']
        self.address_count = spokeo_record['address_count']

    def __str__(self):
        return '{name} {aka}\n{city}\n{relatives}'.format(
            name=self.full_name,
            aka=self.aka(),
            relatives=self.related_to(),
            city=self.top_city())

    def __repr__(self):
        return str(self.raw)

    def top_city(self):
        return self.cities[self.top_city_index]

    def related_to(self):
        return 'Related To:\n\t{family}'.format(family='\n\t'.join(self.family_members))

    def aka(self):
        if len(self.additional_names)>0:
            return '(aka: {akas})'.format(akas='; '.join(self.additional_names))
        else:
            return ''


class City:
    def __init__(self, city: dict):
        self.raw = city
        self.name = city['city']
        self.state = city['state']
        self.postal_code = city['postal_code']
        self.latitude = city['latitude']
        self.longitude = city['longitude']

    def __str__(self):
        return f'{self.name}, {self.state} {self.postal_code}'

    def __repr__(self):
        return str(self.raw)


if __name__ == '__main__':
    pass
