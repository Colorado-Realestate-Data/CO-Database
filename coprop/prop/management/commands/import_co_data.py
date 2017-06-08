import os
import sys
import csv
from coprop.helpers.rest_client import RestClient, RestResponseException

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    help = "Import co-database records from csv file."
    client = None

    def add_arguments(self, parser):
        parser.add_argument('--api-url', action='store', type=str, required=True)
        parser.add_argument('--api-username', action='store', type=str, required=True)
        parser.add_argument('--api-password', action='store', type=str, required=True)
        parser.add_argument('--owners-csv-path', action='store', type=str, required=True)
        parser.add_argument('--accounts-csv-path', action='store', type=str, required=True)
        parser.add_argument('--auction-csv-path', action='store', type=str, required=True)

    def handle(self, *args, **options):
        owners_csv_path = options.get('owners_csv_path')
        accounts_csv_path = options.get('accounts_csv_path')
        auction_csv_path = options.get('auction_csv_path')
        api_url = options.get('api_url')
        api_username = options.get('api_username')
        api_password = options.get('api_password')
        self.client = RestClient(api_url, api_username, api_password)
        for path in (owners_csv_path, accounts_csv_path, auction_csv_path):
            if not path or not os.path.exists(path):
                print('File [{}] Does not exists!'.format(path))
                sys.exit(1)

        print('+++ Start Importing records from ...')
        self.import_data(owners_csv_path, accounts_csv_path, auction_csv_path)
        print("--- Finished!")

    @staticmethod
    def strip_dict(d):
        return {k: v and v.strip() for k, v in d.items()}

    def add_property(self, row):
        address = {
            'street1': ' '.join(
                [row.get('STREETNO'), row.get('DIRECTION'),
                 row.get('STREETNAME'), row.get('DESIGNATION')]).strip() or None,
            'street2': row.get('UNITNUMBER') or None,
            'city': row.get('LOCCITY') or None,
            'zipcode': row.get('PROPZIP') or None,
        }
        data = {
            'parid': row.get('PARCELSEQ'),
            'county': 'Grand',
            'address': address
        }
        try:
            prop = self.client.post('/api/v1/property', data)
        except RestResponseException as exc:
            msg = str(exc.args[2])
            if exc.status_code == 409:
                if 'parid' in msg:
                    res = self.client.get(
                        '/api/v1/property', {'parid': data['parid'],
                                             'county': data['county']})['results']
                    prop = res[0]
                else:
                    print('Skipped adding this property: {}', str(data))
                    return None
            else:
                raise exc
        return prop

    def add_owners(self, row, property_id):
        name = row.get('NAME')
        ownico = row.get('CAREOF')
        address = {
            'street1': row.get('ADDRESS1') or None,
            'street2': row.get('ADDRESS2') or None,
            'city': row.get('CITY') or None,
            'state': row.get('STATE') or None,
            'zipcode': row.get('ZIPCODE') or None,
        }
        data = {
            'name': name,
            'ownico': True if ownico else False,
            'properties': [property_id],
            'addresses': [address]
        }
        if ownico:
            data['other'] = ownico
        return self.client.post('/api/v1/owner', data)

    def add_account(self, row, property_parids):
        parid = row.get('Parcel_ID')
        prop = property_parids.get(parid)
        if not prop:
            print('!!! Unknown parid "{}"!!!'.format(parid))
            return None
        data = {
            'property': prop['id'],
            'tax_year': row.get('Tax_Year') or None,
            'tax_type': row.get('Tax_Type') or None,
            'effective_date': row.get('Effective_Date') or None,
            'amount': row.get('Amount') or None,
            'balance': row.get('Balance') or None,
        }
        try:
            account = self.client.post('/api/v1/account', data)
        except RestResponseException as exc:
            if exc.status_code == 409:
                print('Skipped adding this duplicated account: {}', str(data))
                return None
            elif exc.status_code == 400:
                print('Skipped adding this invalid account: {}', str(data))
                return None
            else:
                raise exc
        return account

    def add_lien_auction(self, row, property_parids):
        parid = row.get('Parcel_ID')
        prop = property_parids.get(parid)
        if not prop:
            print('!!! Unknown parid "{}"!!!'.format(parid))
            return None
        data = {
            'property': prop['id'],
            'name': row.get('Name') or None,
            'face_value': row.get('Face_Value') or None,
            'tax_year': row.get('Tax_Year') or None,
            'winning_bid': row.get('Winning_Bid') or None,
        }
        try:
            auction = self.client.post('/api/v1/lien_auction', data)
        except RestResponseException as exc:
            if exc.status_code == 409:
                print('Skipped adding this duplicated lien_auction: {}', str(data))
                return None
            elif exc.status_code == 400:
                print('Skipped adding this invalid lien_auction: {}', str(data))
                return None
            else:
                raise exc
        return auction

    def import_data(self, owners_csv_path, accounts_csv_path, auction_csv_path):
        print('+ Insert Responder starting....')
        property_parids = {}
        with open(owners_csv_path) as csvfile:
            reader = csv.DictReader(csvfile, delimiter='\t')
            for row in reader:
                print(
                    '+++ Processing Property Row #{}'.format(reader.line_num - 1))
                row = self.strip_dict(row)
                prop = self.add_property(row)
                if not prop:
                    continue
                property_parids[prop.get('parid')] = prop
                self.add_owners(row, prop.get('id'))
        with open(accounts_csv_path) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                print('+++ Processing Account Row #{}'.format(reader.line_num - 1))
                row = self.strip_dict(row)
                self.add_account(row, property_parids)
        with open(auction_csv_path) as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                print('+++ Processing Auction Row #{}'.format(reader.line_num - 1))
                row = self.strip_dict(row)
                self.add_lien_auction(row, property_parids)
