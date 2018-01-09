import os
import sys
import csv
from django.core.management.base import BaseCommand

from coprop.helpers.rest_client import RestClient, RestResponseException


class Command(BaseCommand):

    help = "Import co-database records from csv file."
    client = None
    API_PREFIX = '/{county}/api/v1'

    def add_arguments(self, parser):
        parser.add_argument('--api-url', action='store', type=str, required=True)
        parser.add_argument('--api-username', action='store', type=str, required=True)
        parser.add_argument('--api-password', action='store', type=str, required=True)
        parser.add_argument('--county', action='store', type=str, required=True)
        parser.add_argument('--owners-csv-path', action='store', type=str)
        parser.add_argument('--accounts-csv-path', action='store', type=str)
        parser.add_argument('--auction-csv-path', action='store', type=str)

    def handle(self, *args, **options):
        self.county = options.get('county').lower()
        owners_csv_path = options.get('owners_csv_path')
        accounts_csv_path = options.get('accounts_csv_path')
        auction_csv_path = options.get('auction_csv_path')
        api_url = options.get('api_url')
        api_username = options.get('api_username')
        api_password = options.get('api_password')
        self.client = RestClient(api_url, api_username, api_password)
        any_path = False
        for path in (owners_csv_path, accounts_csv_path, auction_csv_path):
            if path and not os.path.exists(path):
                print('[{}] file does not exists!'.format(path))
                sys.exit(1)
            elif path:
                any_path = True

        if not any_path:
            print('please specify one of this arguments: --owners-csv-path, --accounts-csv-path, --auction-csv-path')
            sys.exit(1)
        print('+++ Start Importing records from ...')
        self.import_data(owners_csv_path, accounts_csv_path, auction_csv_path)
        print("--- Finished!")

    def api_url(self, endpoint):
        prefix = self.API_PREFIX.format(county=self.county).rstrip('/')
        return '{}/{}'.format(prefix, endpoint.lstrip())

    @staticmethod
    def strip_dict(d):
        return {k: v.strip() if isinstance(v, str) else v for k, v in d.items()}

    @staticmethod
    def get_one_of_keys(d, *keys):
        v = [d[k] for k in keys if k in d]
        assert len(v) < 2, '2 keys[{}] exists for {} row'.format(keys, d)
        return v[0] if v else None

    def get_property(self, parid):
        res = self.client.get(self.api_url('property'), {'parid': parid, 'county': self.county})['results']
        return res[0] if res else None

    def add_property(self, row):
        parid = row.get('ACCOUNTNO')
        if not parid:
            print('invalid record! parid is blank!')
            return None
        address = {
            'street1': ' '.join(
                [row.get('STREETNO'), row.get('DIRECTION'),
                 row.get('STREETNAME'), row.get('DESIGNATION')]).strip() or None,
            'street2': row.get('UNITNUMBER') or None,
            'city': row.get('LOCCITY') or None,
            'zipcode': row.get('PROPZIP') or None,
        }
        data = {
            'parid': parid,
            'county': self.county,
            'address': address
        }
        try:
            prop = self.client.post(self.api_url('property'), data)
        except RestResponseException as exc:
            msg = str(exc.args[2])
            if exc.status_code == 409:
                if 'parid' in msg:
                    prop = self.get_property(data['parid'])
                else:
                    print('Skipped adding this property: {}'.format(str(data)))
                    return None
            else:
                raise exc
        return prop

    def add_owners(self, row, property_id):
        name = row.get('NAME')
        if not name:
            print('invalid record! name is blank!')
            return None
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
        return self.client.post(self.api_url('owner'), data)

    def add_account(self, row, property_parids):
        parid = row.get('Parcel_ID')
        if property_parids is None:
            prop = self.get_property(parid)
        else:
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
            account = self.client.post(self.api_url('account'), data)
        except RestResponseException as exc:
            if exc.status_code == 409:
                print('Skipped adding this duplicated account: {}'.format(str(data)))
                return None
            elif exc.status_code == 400:
                print('Skipped adding this invalid account: {}'.format(str(data)))
                return None
            else:
                raise exc
        return account

    def add_lien_auction(self, row, property_parids):
        parid = self.get_one_of_keys(row, 'Parcel_ID','Parcel', 'PARCEL')
        if property_parids is None:
            prop = self.get_property(parid)
        else:
            prop = property_parids.get(parid)
        if not prop:
            print('!!! Unknown parid "{}"!!!'.format(parid))
            return None
        name = self.get_one_of_keys(row, 'Name', 'Primary Name On Account', 'PRIMARY NAME ON ACCOUNT')
        if None in row:
            name = ' '.join([n.strip() for n in (row[None] + [name]) if (n and n.strip())])
        data = {
            'property': prop['id'],
            'name': name,
            'face_value': self.get_one_of_keys(row, 'Face_Value', 'Face Amount', 'FACE AMOUNT') or None,
            'tax_year': self.get_one_of_keys(row, 'Tax_Year') or None,
            'winning_bid': self.get_one_of_keys(row, 'Winning_Bid', 'WinningBid', 'WINNINGPREMIUM') or None,
        }
        try:
            auction = self.client.post(self.api_url('lien_auction'), data)
        except RestResponseException as exc:
            if exc.status_code == 409:
                print('Skipped adding this duplicated lien_auction: {}'.format(str(data)))
                return None
            elif exc.status_code == 400:
                print('Skipped adding this invalid lien_auction: {}'.format(str(data)))
                return None
            else:
                raise exc
        return auction

    def import_data(self, owners_csv_path, accounts_csv_path, auction_csv_path):
        print('+ Insert Responder starting....')
        property_parids = None
        if owners_csv_path:
            property_parids = {}
            with open(owners_csv_path) as csvfile:
                reader = csv.DictReader(csvfile, delimiter='\t')
                new_props = 0
                new_owners = 0
                for row in reader:
                    print('+++ Processing Property Row #{}'.format(reader.line_num - 1))
                    row = self.strip_dict(row)
                    prop = self.add_property(row)
                    if not prop:
                        continue
                    new_props += 1
                    property_parids[prop.get('parid')] = prop
                    owner = self.add_owners(row, prop.get('id'))
                    if owner:
                        new_owners += 1
            print('### {} new property added! ###'.format(new_props))
            print('### {} new owner added! ###'.format(new_owners))
        if accounts_csv_path:
            with open(accounts_csv_path) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=',')
                new_accounts = 0
                for row in reader:
                    print('+++ Processing Account Row #{}'.format(reader.line_num - 1))
                    row = self.strip_dict(row)
                    account = self.add_account(row, property_parids)
                    if account:
                        new_accounts += 1
                print('### {} new account added! ###'.format(new_accounts))
        if auction_csv_path:
            with open(auction_csv_path) as csvfile:
                reader = csv.DictReader(csvfile, delimiter=',')
                new_auctions = 0
                for row in reader:
                    print('+++ Processing Auction Row #{}'.format(reader.line_num - 1))
                    row = self.strip_dict(row)
                    auction = self.add_lien_auction(row, property_parids)
                    if auction:
                        new_auctions += 1
                print('### {} new auction added! ###'.format(new_auctions))
