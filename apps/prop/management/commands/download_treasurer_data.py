import csv
import os
import sys
import time
import glob
import shutil
from datetime import datetime
from io import StringIO

import requests
import functools
from django.conf import settings

from prop.models import LienAuction

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from . import _treasurer_counties as counties

print = functools.partial(print, flush=True)


class Command(BaseCommand):

    help = "download csv records from an treasurer site"
    _county_conf = None
    _general_session = None
    download_path = None
    export_file = None
    county = None
    DOWNLOAD_DIR = 'treasurer-downloads'
    EXPORT_FILE = 'accounts.csv'
    ROUND_WAIT_SECONDS = 0

    @property
    def county_conf(self):
        if self._county_conf is None:
            self._county_conf = counties.default.copy()
            self._county_conf.update(counties.conf[self.county])
        return self._county_conf

    @property
    def general_session(self):
        if self._general_session is None:
            session = requests.session()
            session.get(self.init_url)
            session.post(self.login_url, data=self.county_conf['public_login_data'], allow_redirects=False)
            self._general_session = session
        return self._general_session

    @property
    def ACCOUNT_TX_URL(self):
        return self.county_conf['account_tx_url'] + '?account={account_id}&action=tx'

    @property
    def export_file_path(self):
        return os.path.join(self.download_path, self.county, self.export_file or self.EXPORT_FILE)

    @property
    def download_parts_dir(self):
        return os.path.join(self.download_path, self.county, 'parts')

    def add_arguments(self, parser):
        parser.add_argument('--county', action='store', type=str, required=True,
                            help='valid counties: {}'.format(', '.join(counties.conf.keys())))
        parser.add_argument('--noinput', action='store_true')
        parser.add_argument('--export-file', action='store', type=str)
        parser.add_argument('--download-path', action='store', type=str)
        parser.add_argument('--download-dir', action='store', type=str, default=self.DOWNLOAD_DIR)
        parser.add_argument('--round-wait-seconds', action='store', type=int, default=self.ROUND_WAIT_SECONDS)
        parser.add_argument('--clean', action='store_true')
        parser.add_argument('--merge', action='store_true')

    def init_vars(self, *args, **options):
        self.county = options.get('county')
        if self.county not in counties.conf:
            print('!!! Invalid county [{}]! valid counties are: [{}]'.format(self.county, ', '.join(counties.conf.keys())))
            sys.exit(1)
        self.base_url = self.county_conf['site']
        self.noinput = options.get('noinput')
        self.round_wait_seconds = options.get('round_wait_seconds')
        self.export_file = options.get('export_file')
        self.download_path = os.path.join(options.get('download_path') or settings.BASE_DIR,
                                          options.get('download_dir') or self.DOWNLOAD_DIR)
        self.init_url = urljoin(self.base_url, self.county_conf['init_url'])
        self.login_url = urljoin(self.base_url, self.county_conf['login_url'])
        self.account_tx_url = urljoin(self.base_url, self.ACCOUNT_TX_URL)


    def handle(self, *args, **options):
        try:
            self._handle(*args, **options)
        except KeyboardInterrupt:
            print('Canceled!')
            sys.exit(1)

    def _handle(self, *args, **options):
        self.init_vars(*args, **options)
        if options.get('merge'):
            return self.merge_parts()
        if options.get('clean'):
            shutil.rmtree(self.download_parts_dir)

        if os.path.exists(self.download_parts_dir):
            if glob.glob1(self.download_parts_dir, '*.csv') and not self.noinput:
                confirm = input('previous download parts already exists!\ndo you want to continue previous or restart?'
                                '([C]Countine / [r]Restart) ')
                if (confirm.lower() or 'c') == 'r':
                    shutil.rmtree(self.download_parts_dir)
                    os.makedirs(self.download_parts_dir)
        else:
            os.makedirs(self.download_parts_dir)

        account_ids = LienAuction.objects.order_by('property__parid').values_list('property__parid',
                                                                                  flat=True).distinct()
        print('+++ starting download [{}] accounts ...'.format(len(account_ids)))
        for account_id in account_ids:
            try:
                self.download_account_tx(account_id)
            except Exception:
                print('!!! Failed to download [{}] account.'.format(account_id))
            time.sleep(self.round_wait_seconds)
        print('+++ Finished [{}] accounts.'.format(len(account_ids)))

    @staticmethod
    def _standardize_row(row):

        row['Amount'] = ''.join(c for c in row['Amount'] if c not in '$,()')
        row['Balance'] = ''.join(c for c in row['Balance'] if c not in '$,()')
        dt = row['Effective_Date']
        try:
            dt = datetime.strptime(dt, '%m/%d/%y').date().strftime('%Y-%m-%d')
        except ValueError:
            dt = ''
        if not dt:
            print('Invalid Effective_Date: [{}] for account [{}]'.format(row['Effective_Date'], row['Parcel_ID']))
        row['Effective_Date'] = dt
        return row

    def download_account_tx(self, account_id):
        print('+++ Downloading Account transactions of [{}]'.format(account_id))
        csv_path = os.path.join(self.download_parts_dir, '{}.csv'.format(account_id))
        if os.path.exists(csv_path):
            print('!!! Skipped to download! records for [{}] account already downloaded!'.format(account_id))
            return

        tx_url = self.account_tx_url.format(account_id=account_id)

        response = self.general_session.get(tx_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table', attrs={'class': 'account stripe'})
        if not table:
            print('!!! The account could not be found for [{}]'.format(account_id))
            return
        trs = table.find_all('tr')[1:]
        data_temp = StringIO()
        csv_columns = ['Parcel_ID', 'Amount', 'Tax_Year', 'Tax_Type', 'Effective_Date', 'Balance']
        writer = csv.DictWriter(data_temp, fieldnames=csv_columns)
        writer.writeheader()
        for tr in trs:
            tds = tr.find_all('td')
            tax_year = tds[0].text
            tax_type = tds[1].text
            effective_date = tds[2].text
            amount = tds[3].text.replace(',', '').replace('$', '')
            balance = tds[4].text
            row = self._standardize_row({'Parcel_ID': account_id, 'Amount': amount, 'Tax_Year': tax_year, 'Tax_Type': tax_type,
                                         'Effective_Date': effective_date, 'Balance': balance})
            writer.writerow(row)
        data_temp.seek(0)
        with open(csv_path, 'w') as csv_file:
            csv_file.write(data_temp.read())

    def merge_parts(self):
        if not os.path.exists(self.download_parts_dir):
            print('!!! Cannot merge files! part files not downloaded yet!')
            return
        files = glob.glob1(self.download_parts_dir, '*.csv')
        if not files:
            print('!!! Cannot merge files! parts files not downloaded yet!')
            return
        if os.path.exists(self.export_file_path) and not self.noinput:
            confirm = input(
                '!!! Export file ({}) already exists!\nDo you want to replace?(N/y) '.format(self.export_file_path))
            if (confirm.lower() or 'n') == 'n':
                return
        files.sort()
        print('+++ Merging [{}] files ...'.format(len(files)))
        with open(self.export_file_path, 'wb') as export_file:
            included_header = False
            for f in files:
                file_path = os.path.join(self.download_parts_dir, f)
                with open(file_path, 'rb') as fin:
                    header = next(fin)  # skip header
                    if not included_header:
                        export_file.write(header)
                        included_header = True
                    export_file.write(fin.read())
        print('***** Merged to: [{}]'.format(self.export_file_path))
