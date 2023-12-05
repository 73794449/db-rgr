import re
import time
from datetime import datetime
import faker
from psycopg2 import connect
import phonenumbers

use_faker = True
faker.Faker.seed(time.time())
fake = faker.Faker()


def verify_value(selected_table, selected_param, entered_param, typeof) -> bool:
    format_for_date = "%Y-%m-%d"
    format_for_timestamp = "%Y-%m-%d %H-%M-%S"
    if (((selected_table == 1 and selected_param == 2) or (selected_table == 5 and selected_param == 6) or
         (selected_table == 6 and selected_param == 6)) and
            entered_param not in ['A+', 'O+', 'B+', 'AB+', 'A-', 'O-', 'B-', 'AB-']):
        # BloodBag.BloodType, Recipient.BloodTypeNeeded, Donor.BloodType
        return False
    if ((selected_table == 1 and selected_param == 3) and
            not (17 < int(entered_param) < 24)):  # BloodBag.StorageTemperature
        return False
    if typeof == 'date':
        try:
            check_date = bool(datetime.strptime(entered_param, format_for_date))
        except ValueError:
            check_date = False
        return check_date
    if typeof == 'timestamp without time zone':
        try:
            check_date = bool(datetime.strptime(entered_param, format_for_timestamp))
        except ValueError:
            check_date = False
        return check_date
    if (selected_table == 3 and selected_param == 4) or (selected_table == 5 and
                                                         selected_param == 5) or (selected_table == 6
                                                                                  and selected_param == 5):
        # ContactNumber
        phone_number = phonenumbers.parse(entered_param)
        if not phonenumbers.is_possible_number(phone_number):
            return False
    if (typeof == 'integer' or typeof == 'smallint' or typeof == 'bigint') and isinstance(entered_param, str):
        if not (entered_param.isnumeric()):
            return False
    if typeof == 'text' and not (selected_table == 3 and selected_param == 3):  # Address can contain all symbols
        if not re.search("^[A-Z][a-z]", entered_param):
            return False
    return True


def generate_first_name() -> str:
    if use_faker:
        res = "'" + fake.first_name() + "'" + ","
    else:
        res = (f"((array['Ivan', 'Bora', 'Jorik','Olesia', "
               f"'Patrick', 'John', 'Steven', 'Nastya'])[floor(random()*8+1)],")
    return res


def generate_last_name() -> str:
    if use_faker:
        res = "'" + fake.last_name() + "'" + ","
    else:
        res = (f"(array['Terentiev', 'Zorev', 'Smith','Miller', "
               f"'Williams', 'Davis', 'Steven', 'Garcia'])[floor(random()*8+1)],")
    return res


def generate_random_company() -> str:
    if use_faker:
        res = "'" + fake.company() + "'" + ","
    else:
        res = (f"(array['HelpAnother', 'BeDonor', 'Back4Blood','Bloody', 'MealsForBlood', "
               f"'MeatHook', 'TheCakeislie','Bloodborn'])[floor(random()*8+1)],")
    return res


def generate_location() -> str:
    if use_faker:
        res = "'" + fake.country() + ", " + fake.city() + ", " + fake.street_address() + "'" + ", "
    else:
        res = f"(array['Ukraine', 'USA', 'France','Germany', 'UK', 'Poland', 'Canada', 'India'])[floor(random()*8+1)],"
    return res


class Model:
    tables = {
        1: {1: 'BloodBag',
            2: {1: 'BagID', 2: 'BloodType', 3: 'StorageTemperature'}},
        2: {1: 'BloodBag-BloodDonation',
            2: {1: 'BloodDonationID', 2: 'BloodBagID'}},
        3: {1: 'BloodBank',
            2: {1: 'BloodBankID', 2: 'Name', 3: 'Location', 4: 'ContactNumber', 5: 'TotalDonations',
                6: 'BloodDonationID'}},
        4: {1: 'BloodDonation',
            2: {1: 'DonationID', 2: 'DonationDate', 3: 'DonationTime', 4: 'DonorID', 5: 'DonationStatus'}},
        5: {1: 'Donor',
            2: {1: 'DonorID', 2: 'FirstName', 3: 'LastName', 4: 'DateOfBirth',
                5: 'ContactNumber', 6: 'BloodType'}},
        6: {1: 'Recipient',
            2: {1: 'RecipientID', 2: 'FirstName', 3: 'LastName', 4: 'DateOfBirth',
                5: 'ContactNumber', 6: 'BloodTypeNeeded', 7: 'BloodBagID'}}
    }
    tables_for_search = {
        1: {1: 'BloodDonation',
            2: {1: 'WHERE BloodBag.BloodType', 2: 'OR BloodBag.BloodType', 3: 'AND DonationStatus'},
            3: 'SELECT "DonationID", "DonationDate", "DonationStatus" FROM "BloodDonation" '
               'INNER JOIN "BloodBag-BloodDonation" ON "BloodDonationID"="DonationID" '
               'INNER JOIN "BloodBag" ON '
               '"BloodBag-BloodDonation"."BloodBagID" = "BloodBag"."BagID" '
               f'WHERE ("BloodBag"."BloodType" = %s '
               f'OR "BloodBag"."BloodType" = %s) AND '
               f'"BloodDonation"."DonationStatus" = %s'},
        2: {1: 'Donor',
            2: {1: 'WHERE BloodDonation.DonationStatus', 2: 'AND Donor.FirstName', 3: 'AND Donor.ContactNumber'},
            3: 'SELECT "Donor"."DonorID", "Donor"."FirstName", '
               '"Donor"."LastName" FROM "Donor" INNER JOIN '
               '"BloodDonation" ON "Donor"."DonorID" = "BloodDonation"."DonorID" '
               f'WHERE "BloodDonation"."DonationStatus" = %s AND '
               f'("Donor"."FirstName" = %s AND '
               f'"Donor"."ContactNumber" = %s) '
               'GROUP BY "Donor"."DonorID"'},
        3: {1: 'Recipient',
            2: {1: 'WHERE BloodBag.BloodType', 2: 'AND Recipient.FirstName', 3: 'AND Recipient.LastName'},
            3: 'SELECT "RecipientID", "FirstName", "LastName" FROM "Recipient" '
               'INNER JOIN "BloodBag" ON "Recipient"."BloodBagID" = "BloodBag"."BagID" '
               f'WHERE "BloodBag"."BloodType" = %s '
               f'AND ("Recipient"."FirstName" = %s '
               f'AND "Recipient"."LastName" = %s) GROUP BY "RecipientID"'},
    }
    tables_for_rand = {
        1: f"INSERT INTO \"BloodBag\" ( \"BloodType\", \"StorageTemperature\") VALUES "
           f"((array['A+', 'O+', 'B+','AB+', 'A-', 'O-', 'B-', 'AB-'])[floor(random()*8+1)], floor(random()*3 "
           f"+ 18))",
        2: f"INSERT INTO \"BloodBag-BloodDonation\" (\"BloodDonationID\", \"BloodBagID\") VALUES ("
           f"(SELECT \"DonationID\" FROM \"BloodDonation\" ORDER BY RANDOM() LIMIT 1),"
           f"(SELECT \"BagID\" FROM \"BloodBag\" ORDER BY RANDOM() LIMIT 1))",
        3: f"INSERT INTO \"BloodBank\" (\"Name\", \"Location\", \"ContactNumber\", \"TotalDonations\","
           f" \"BloodDonationID\") VALUES(" +
           generate_random_company() +
           generate_location() +
           f"to_char(random() * 10000000000, 'FM\"+\"000\"\"000\"\"0000'),"
           f"floor(random()*1000+10),"
           f"(SELECT \"DonationID\" FROM \"BloodDonation\" ORDER BY RANDOM() LIMIT 1))",
        4: f"INSERT INTO \"BloodDonation\" (\"DonationDate\", \"DonationTime\",\"DonorID\","
           f"\"DonationStatus\") VALUES("
           f"date '2077-01-01' + (random() * (date '2000-11-11' - date '2077-01-01'))::int,"
           f"timestamp '2077-01-01' + random() * (timestamp '2000-11-11' - timestamp '2077-01-01'),"
           f"(SELECT \"DonorID\" FROM \"Donor\" ORDER BY RANDOM() LIMIT 1),"
           f"(array['Done', 'Planned'])[floor(random()*1+1)])",
        5: f"INSERT INTO \"Donor\" (\"FirstName\", \"LastName\", \"DateOfBirth\", \"ContactNumber\", "
           f"\"BloodType\")"
           f"VALUES(" +
           generate_first_name() +
           generate_last_name() +
           f"date '2077-01-01' + (random() * (date '2000-11-11' - date '2077-01-01'))::int,"
           f"to_char(random() * 10000000000, 'FM\"+\"000\"\"000\"\"0000'),"
           f"(array['A+', 'O+', 'B+','AB+', 'A-', 'O-', 'B-', 'AB-'])[floor(random()*8+1)])",
        6: f"INSERT INTO \"Recipient\" (\"FirstName\", \"LastName\", \"DateOfBirth\","
           f" \"ContactNumber\", \"BloodTypeNeeded\", \"BloodBagID\") VALUES (" +
           generate_first_name() +
           generate_last_name() +
           f"date '2077-01-01' + (random() * (date '2000-11-11' - date '2077-01-01'))::int,"
           f"to_char(random() * 10000000000, 'FM\"+\"000\"\"000\"\"0000'),"
           f"(array['A+', 'O+', 'B+','AB+', 'A-', 'O-', 'B-', 'AB-'])[floor(random()*8+1)],"
           f"NULL)"
    }

    def __init__(self, connection_settings):
        self.connection = connect(
            dbname=connection_settings['dbname'],
            user=connection_settings['user'],
            password=connection_settings['password'],
            host=connection_settings['host'],
            port=connection_settings['port']
        )

    def execute(self, execute_string, params=None):
        cursor = self.connection.cursor()
        cursor.execute(execute_string, params)
        self.connection.commit()
        return cursor

    def get_table(self, selected_table):
        return self.execute(f'SELECT * FROM "{self.tables[selected_table][1]}"')

    def get_params(self, selected_table):
        return self.tables[selected_table][2]

    def get_params_for_search(self, selected_table):
        return self.tables_for_search[selected_table][2]

    def search(self, selected_table, entered_params):
        start = time.time()
        res = self.execute(self.tables_for_search[selected_table][3],
                           (str(entered_params[1]), str(entered_params[2]), str(entered_params[3])))
        end = time.time()
        return res, (end - start)

    def get_typeof(self, selected_table, selected_param):
        cursor = self.execute(f'SELECT data_type FROM information_schema.columns WHERE table_schema = \'public\' AND '
                              f'table_name = \'{self.tables[selected_table][1]}\' AND '
                              f'column_name = \'{self.tables[selected_table][2][selected_param]}\'')
        from_cursor = cursor.fetchall()
        return from_cursor[0][0]

    def edit_param_to_real_string(self, selected_table, selected_param, entered_param):
        typeof = self.get_typeof(selected_table, selected_param)
        if typeof == 'text' or typeof == 'date' or typeof == 'timestamp without time zone':
            return "'" + entered_param + "'"
        return entered_param

    def add_table(self, selected_table, entered_params) -> bool:
        Verification = True
        params_string = ', '.join(f'"{str(self.tables[selected_table][2][x])}"' for x in self.tables[selected_table][2])
        for i in entered_params:
            entered_params[i] = self.edit_param_to_real_string(selected_table, i, entered_params[i])
            Verification = verify_value(selected_table, i, entered_params[i], self.get_typeof(selected_table, i))
        entered_params_string = ', '.join(str(entered_params[x]) for x in entered_params)
        if Verification:
            self.execute(f'INSERT INTO public."{self.tables[selected_table][1]}" ' +
                         f'({params_string})'
                         f'VALUES({entered_params_string})')
        return Verification

    def check_id(self, selected_table, selected_id) -> bool:
        selected_id_real_num = verify_value(selected_table, 1, selected_id, 'integer')
        if selected_id_real_num:
            cursor = self.execute(f'SELECT FROM public."{self.tables[selected_table][1]}" WHERE'
                                  f' "{self.tables[selected_table][2][1]}" = {selected_id}')
            from_cursor = cursor.fetchall()
            if len(from_cursor) == 0:
                return False
        else:
            return False
        return True

    def delete_table(self, selected_table, selected_id) -> bool:
        Verification = self.check_id(selected_table, selected_id)
        if Verification:
            self.execute(f'DELETE FROM public."{self.tables[selected_table][1]}" '
                         f'WHERE "{self.tables[selected_table][2][1]}" = {selected_id}')
        return Verification

    def edit_table(self, selected_table, selected_id, selected_param, entered_param) -> bool:
        entered_param = self.edit_param_to_real_string(selected_table, selected_param, entered_param)
        Verification = verify_value(selected_table, selected_param, entered_param, self.get_typeof(selected_table,
                                                                                                   selected_param))
        if Verification:
            Verification = self.check_id(selected_table, selected_id)
            if Verification:
                self.execute(f'UPDATE public."{self.tables[selected_table][1]}" SET '
                             f'"{self.tables[selected_table][2][selected_param]}" = {entered_param} WHERE '
                             f'"{self.tables[selected_table][2][1]}" = {selected_id}')
        return Verification

    def randomize_table(self, selected_table, count):
        for _ in range(count):
            if use_faker:
                tables_for_rand = {  # I did not find something like reinit, so it looks like this for faker
                    1: f"INSERT INTO \"BloodBag\" ( \"BloodType\", \"StorageTemperature\") VALUES "
                       f"((array['A+', 'O+', 'B+','AB+', 'A-', 'O-', 'B-', 'AB-'])[floor(random()*8+1)], "
                       f"floor(random()*3 + 18))",
                    2: f"INSERT INTO \"BloodBag-BloodDonation\" (\"BloodDonationID\", \"BloodBagID\") VALUES ("
                       f"(SELECT \"DonationID\" FROM \"BloodDonation\" ORDER BY RANDOM() LIMIT 1),"
                       f"(SELECT \"BagID\" FROM \"BloodBag\" ORDER BY RANDOM() LIMIT 1))",
                    3: f"INSERT INTO \"BloodBank\" (\"Name\", \"Location\", \"ContactNumber\", \"TotalDonations\","
                       f" \"BloodDonationID\") VALUES(" +
                       generate_random_company() +
                       generate_location() +
                       f"to_char(random() * 10000000000, 'FM\"+\"000\"\"000\"\"0000'),"
                       f"floor(random()*1000+10),"
                       f"(SELECT \"DonationID\" FROM \"BloodDonation\" ORDER BY RANDOM() LIMIT 1))",
                    4: f"INSERT INTO \"BloodDonation\" (\"DonationDate\", \"DonationTime\",\"DonorID\","
                       f"\"DonationStatus\") VALUES("
                       f"date '2077-01-01' + (random() * (date '2000-11-11' - date '2077-01-01'))::int,"
                       f"timestamp '2077-01-01' + random() * (timestamp '2000-11-11' - timestamp '2077-01-01'),"
                       f"(SELECT \"DonorID\" FROM \"Donor\" ORDER BY RANDOM() LIMIT 1),"
                       f"(array['Done', 'Planned'])[floor(random()*1+1)])",
                    5: f"INSERT INTO \"Donor\" (\"FirstName\", \"LastName\", \"DateOfBirth\", \"ContactNumber\", "
                       f"\"BloodType\")"
                       f"VALUES(" +
                       generate_first_name() +
                       generate_last_name() +
                       f"date '2077-01-01' + (random() * (date '2000-11-11' - date '2077-01-01'))::int,"
                       f"to_char(random() * 10000000000, 'FM\"+\"000\"\"000\"\"0000'),"
                       f"(array['A+', 'O+', 'B+','AB+', 'A-', 'O-', 'B-', 'AB-'])[floor(random()*8+1)])",
                    6: f"INSERT INTO \"Recipient\" (\"FirstName\", \"LastName\", \"DateOfBirth\","
                       f" \"ContactNumber\", \"BloodTypeNeeded\", \"BloodBagID\") VALUES (" +
                       generate_first_name() +
                       generate_last_name() +
                       f"date '2077-01-01' + (random() * (date '2000-11-11' - date '2077-01-01'))::int,"
                       f"to_char(random() * 10000000000, 'FM\"+\"000\"\"000\"\"0000'),"
                       f"(array['A+', 'O+', 'B+','AB+', 'A-', 'O-', 'B-', 'AB-'])[floor(random()*8+1)],"
                       f"NULL)"
                }
                self.execute(tables_for_rand[selected_table])
            else:
                self.execute(self.tables_for_rand[selected_table])
