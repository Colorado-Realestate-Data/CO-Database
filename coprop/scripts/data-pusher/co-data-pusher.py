import sys
import csv
import config
from co_rest_client import RestClient, RestResponseException

client = RestClient(config.API_URL, config.API_USERNAME, config.API_PASSWORD)


def strip_dict(d):
    return {k: v and v.strip() for k, v in d.items()}


def add_property(row):
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
        prop = client.post('/api/v1/property', data)
    except RestResponseException as exc:
        msg = str(exc.args[2])
        if exc.status_code == 409:
            if 'parid' in msg:
                res = client.get(
                    '/api/v1/property', {'parid': data['parid'],
                                         'county': data['county']})['results']
                prop = res[0]
            else:
                print('Skipped adding this property: {}', str(data))
                return None
        else:
            raise exc
    return prop


def add_owners(row, property_id):
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
    return client.post('/api/v1/owner', data)


def add_account(row, property_parids):
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
        account = client.post('/api/v1/account', data)
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


def add_lien_auction(row, property_parids):
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
        auction = client.post('/api/v1/lien_auction', data)
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


def main():
    if len(sys.argv) != 4:
        print('Invalid parameters! \nUsage: python co-data-pusher2.py '
              '<PROPERTY_OWNERS_FILE_PATH> <ACCOUNTS_FILE_PATH> '
              '<AUCTION_FILE_PATH>')
        sys.exit(1)
    owners_csv_path = sys.argv[1]
    accounts_csv_path = sys.argv[2]
    auction_csv_path = sys.argv[3]
    property_parids = {}
    with open(owners_csv_path) as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for row in reader:
            print(
                '+++ Processing Property Row #{}'.format(reader.line_num - 1))
            row = strip_dict(row)
            prop = add_property(row)
            if not prop:
                continue
            property_parids[prop.get('parid')] = prop
            add_owners(row, prop.get('id'))
    with open(accounts_csv_path) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            print('+++ Processing Account Row #{}'.format(reader.line_num - 1))
            row = strip_dict(row)
            add_account(row, property_parids)
    with open(auction_csv_path) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            print('+++ Processing Auction Row #{}'.format(reader.line_num - 1))
            row = strip_dict(row)
            add_lien_auction(row, property_parids)


if __name__ == '__main__':
    main()
