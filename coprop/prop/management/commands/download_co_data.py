import os
import re
import sys
import csv
import time
import shutil
from threading import Thread

import math
import requests
import functools
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from bs4 import BeautifulSoup
from django.utils import timezone
from django.core.management.base import BaseCommand


print = functools.partial(print, flush=True)


class Command(BaseCommand):

    help = "download csv records from http://assessor.co.{COUNTY}.co.us site"
    _general_session = None

    download_path = None
    county = None
    counter = 0
    REPORT_TEMPLATE_ID = 'tax.account.extract.AccountPublic'
    INIT_URL = 'http://assessor.co.{county}.co.us/assessor/web/'
    LOGIN_URL = 'http://assessor.co.{county}.co.us/assessor/web/loginPOST.jsp'
    SUBMIT_SEARCH_URL = 'http://assessor.co.{county}.co.us/assessor/taxweb/results.jsp'
    REPORT_URL = 'http://assessor.co.{county}.co.us/assessor/eagleweb/report.jsp'
    BASE_URL = 'http://assessor.co.grand.co.us/assessor/eagleweb/'
    DOWNLOAD_DIR = 'co-downloads'
    CHECK_REPORT_INTERVAL = 5
    PIVOT_INIT_VALUE = 1000
    THREADS_COUNT = 30

    @property
    def general_session(self):
        if self._general_session is None:
            session = requests.session()
            session.get(self.init_url)
            session.post(self.login_url, data={'guest': 'true', 'submit': 'Enter EagleWeb'}, allow_redirects=False)
            self._general_session = session
        return self._general_session

    @property
    def GENERATE_REPORT_URL(self):
        return self.REPORT_URL + '?templateId={}&sn=1&generate=true'.format(self.REPORT_TEMPLATE_ID)

    @property
    def CHECK_REPORT_URL(self):
        return self.REPORT_URL + '?display=table'

    @property
    def download_temp_dir(self):
        return os.path.join(self.download_path, 'tmp', self.county)

    def add_arguments(self, parser):
        parser.add_argument('--county', action='store', type=str, required=True)
        parser.add_argument('--download-path', action='store', type=str)
        parser.add_argument('--download-dir', action='store', type=str, default=self.DOWNLOAD_DIR)
        parser.add_argument('--check-report-interval', action='store', type=int, default=self.CHECK_REPORT_INTERVAL)
        parser.add_argument('--pivot-init', action='store', type=int, default=self.PIVOT_INIT_VALUE)
        parser.add_argument('--threads', action='store', type=int, default=self.THREADS_COUNT)
        parser.add_argument('--noinput', action='store_true')

    def handle(self, *args, **options):
        self.finished_counter = 0
        self.county = options.get('county')
        self.threads = options.get('threads')
        self.check_report_interval = options.get('check_report_interval')
        self.pivot_init = options.get('pivot_init')
        self.download_path = os.path.join(options.get('download_path') or '',
                                          options.get('download_dir') or self.DOWNLOAD_DIR)
        self.init_url = self.INIT_URL.format(county=self.county)
        self.login_url = self.LOGIN_URL.format(county=self.county)
        self.submit_search_url = self.SUBMIT_SEARCH_URL.format(county=self.county)
        self.generate_report_url = self.GENERATE_REPORT_URL.format(county=self.county)
        self.check_report_url = self.CHECK_REPORT_URL.format(county=self.county)
        if os.path.exists(self.download_temp_dir):
            if not options.get('noinput'):
                confirm = input('tmp directory already exists! we want to delete this directory. Are you agree?[N/y] ')
                if (confirm.lower() or 'n') != 'y':
                    print('Canceled!')
                    return
            shutil.rmtree(self.download_temp_dir)
        os.makedirs(self.download_temp_dir)
        print('++ Scrapping Total Pages ... ==> ', end='')
        self.total_page = self._scrap_total_page(0, None)
        self.pages_per_thread = int(math.ceil(self.total_page / self.threads))
        print('OK')
        print('++ Distributing downloads [{}] pages between [{}] threads ...'.format(self.total_page, self.threads))
        print('++ [pages_per_thread = {}]'.format(self.pages_per_thread))
        # print(self._scrap_total_page(0, 6))
        # return
        start_value = 0
        threads = []
        while True:
            print('++ Discovering best actual value from [{}] ...'.format(start_value))
            t1 = timezone.now()
            next_value = self.discover_best_actual_value(start_value, pivot=self.pivot_init)
            duration = (timezone.now() - t1).total_seconds()
            print('++ Discovered [{}] for [{}] in [{}] Seconds'.format(next_value, start_value, duration))
            t = Thread(target=self.download_range_data, args=(start_value, next_value))
            threads.append(t)
            t.start()
            if next_value is None:
                break
            start_value = next_value + 1

        for thread in threads:
            thread.join()

    def discover_best_actual_value(self, start_value, pivot=1000):
        lower_bound = start_value
        upper_bound = start_value + pivot
        max_upper_bound = None
        p = None
        while True:
            if upper_bound == lower_bound:
                return upper_bound

            prev_p = p
            p = self._scrap_total_page(start_value, upper_bound)
            if p == 0:
                return None
            if (max_upper_bound is None) and (p == prev_p):
                if self._scrap_total_page(upper_bound, None) == 0:
                    return None

            if 0 <= p - self.pages_per_thread <= 1:
                return upper_bound
            if p < self.pages_per_thread:
                if max_upper_bound is None:
                    lower_bound, upper_bound = upper_bound, 2 * upper_bound - lower_bound
                else:
                    lower_bound = upper_bound
                    upper_bound = upper_bound + (max_upper_bound - upper_bound) // 2
            if p > self.pages_per_thread:
                max_upper_bound = upper_bound
                upper_bound = lower_bound + (upper_bound - lower_bound) // 2

    def download_range_data(self, start_value, end_value):
        start_time = timezone.now()
        range_str = '[{} - {}]'.format(start_value, end_value)
        print('+++ {}: Starting at [{}] ...'.format(range_str, start_time))

        print('+++ {}: Signing in as a [guest]...'.format(range_str))
        session = requests.session()
        session.get(self.init_url)
        session.post(self.login_url, data={'guest': 'true', 'submit': 'Enter EagleWeb'}, allow_redirects=False)
        print('+++ {}: Submitting form ...'.format(range_str))
        data = {}
        if start_value is not None:
            data['accountValueIDStart'] = str(start_value)
        if end_value is not None:
            data['accountValueIDEnd'] = str(end_value)
        if not data:
            raise Exception('Data Cannot be empty in submit form!')

        search_result = session.post(self.submit_search_url, data=data)
        if 'No results found for query' in search_result:
            print('NO RESULT')
            return
        print('+++ {}: Generating Report ...'.format(range_str))
        session.get(self.generate_report_url)
        while True:
            check_result = session.get(self.check_report_url).text
            if 'Your report is being generated' in check_result:
                time.sleep(self.check_report_interval)
                continue
            print('+++ {}: Downloading Report ...'.format(range_str))
            bs = BeautifulSoup(check_result, 'html.parser')
            download_endpoint = bs.find('a').get('href')
            download_url = urljoin(self.BASE_URL, download_endpoint)
            destfile = os.path.join(self.download_temp_dir, '{}-{}.csv'.format(start_value, end_value))
            self._download_file(session, download_url, destfile)
            break
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        self.finished_counter += 1
        print('+++ {}: Finished at [{}] - Duration={} Seconds!'.format(range_str, end_time, duration))

    def _download_file(self, session, url, destfile):
        r = session.get(url, stream=True)
        if r.status_code == 200:
            with open(destfile, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        else:
            raise Exception('Cannot Download File {}, to be saved in {}'.format(url, destfile))

    def _scrap_total_page(self, start_value, end_value, session=None):
        range_str = '[{} - {}]'.format(start_value, end_value)
        session = session or self.general_session
        data = {}
        if start_value is not None:
            data['accountValueIDStart'] = str(start_value)
        if end_value is not None:
            data['accountValueIDEnd'] = str(end_value)
        if not data:
            raise Exception('Data Cannot be empty in submit form!')
        time.sleep(0.5)
        search_result = session.post(self.submit_search_url, data=data).text
        if 'No results found for query' in search_result:
            return 0
        bs = BeautifulSoup(search_result, 'html.parser')
        pagination_title = bs.find(id='middle').find(text=re.compile('^Showing .+ results on .+ page'))
        if not pagination_title:
            raise Exception('!!! {}: Cannot scrap pagination title'.format(range_str))
        re.findall('\d+', pagination_title)
        pages = re.findall('(\d+) page', pagination_title)
        if not pages:
            raise Exception('!!! {}: Cannot scrap total pages'.format(range_str))
        return int(pages[0])

