import os
import re
import sys
import time
import glob
import math
import shutil
import requests
import traceback
import functools
from django.conf import settings
from retrying import retry
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin
from bs4 import BeautifulSoup
from django.utils import timezone
from django.core.management.base import BaseCommand

from . import counties

print = functools.partial(print, flush=True)


class Command(BaseCommand):

    help = "download csv records from an assessor site"
    _county_conf = None
    _general_session = None
    _finished_counter = 0
    records_per_page = None
    is_finished_parts = False
    start_value = 0
    next_value = None
    failed_parts = []
    download_path = None
    export_file = None
    county = None
    DOWNLOAD_DIR = 'co-downloads'
    EXPORT_FILE = 'total.csv'
    CHECK_REPORT_INTERVAL = 5
    PIVOT_INIT_VALUE = 1000
    PARTS_COUNT = 30
    SHOW_INFO_INTERVAL = 10
    ROUND_WAIT_SECONDS = 300
    PAGES_DELTA = 1

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
    def GENERATE_REPORT_URL(self):
        return self.county_conf['report_url'] + '?templateId={}&sn=1&generate=true'.format(
            self.county_conf['report_template_id'])

    @property
    def CHECK_REPORT_URL(self):
        return self.county_conf['report_url'] + '?display=table'

    @property
    def download_parts_dir(self):
        return os.path.join(self.download_path, self.county, 'parts')

    @property
    def export_file_path(self):
        return os.path.join(self.download_path, self.county, self.export_file or self.EXPORT_FILE)

    def add_arguments(self, parser):
        parser.add_argument('--county', action='store', type=str, required=True,
                            help='valid counties: {}'.format(', '.join(counties.conf.keys())))
        parser.add_argument('--export-file', action='store', type=str)
        parser.add_argument('--download-path', action='store', type=str)
        parser.add_argument('--download-dir', action='store', type=str, default=self.DOWNLOAD_DIR)
        parser.add_argument('--check-report-interval', action='store', type=int, default=self.CHECK_REPORT_INTERVAL)
        parser.add_argument('--parts', action='store', type=int, default=self.PARTS_COUNT)
        parser.add_argument('--round-wait-seconds', action='store', type=int, default=self.ROUND_WAIT_SECONDS)
        parser.add_argument('--show-failed-parts', action='store_true')
        parser.add_argument('--pages-delta', action='store', type=int, default=self.PAGES_DELTA)
        parser.add_argument('--use-thread', action='store_true')
        parser.add_argument('--noinput', action='store_true')
        parser.add_argument('--clean', action='store_true')
        parser.add_argument('--merge', action='store_true')

    def handle(self, *args, **options):
        try:
            self._handle(*args, **options)
        except KeyboardInterrupt:
            print('Canceled!')
            sys.exit(1)

    def init_vars(self, *args, **options):
        self._finished_counter = 0
        self.county = options.get('county')
        if self.county not in counties.conf:
            print('!!! Invalid county [{}]! valid counties are: [{}]'.format(self.county, ', '.join(counties.conf.keys())))
            sys.exit(1)
        self.base_url = self.county_conf['site']
        self.pages_delta = options.get('pages_delta')
        self.parts = options.get('parts')
        self.noinput = options.get('noinput')
        self.use_thread = options.get('use_thread')
        self.round_wait_seconds = options.get('round_wait_seconds')
        self.export_file = options.get('export_file')
        self.check_report_interval = options.get('check_report_interval')
        self.download_path = os.path.join(options.get('download_path') or settings.BASE_DIR,
                                          options.get('download_dir') or self.DOWNLOAD_DIR)
        self.init_url = urljoin(self.base_url, self.county_conf['init_url'])
        self.login_url = urljoin(self.base_url, self.county_conf['login_url'])
        self.submit_search_url = urljoin(self.base_url, self.county_conf['submit_search_url'])
        self.generate_report_url = urljoin(self.base_url, self.GENERATE_REPORT_URL)
        self.check_report_url = urljoin(self.base_url, self.CHECK_REPORT_URL)

    @staticmethod
    def _find_gaps(sorted_parts):
        gaps = []
        prev_s = prev_n = None
        for s, n in sorted_parts:
            if (prev_s is not None) and (s != prev_n + 1):
                gaps.append((prev_n + 1, s - 1))
            prev_s = s
            prev_n = n
        return gaps

    def init_resume_vars(self):
        self.start_value = 0
        self.is_finished_parts = False
        self.failed_parts = []
        if not os.path.exists(self.download_parts_dir):
            return
        parts = [tuple(map(int, f[:-4].split('-'))) for f in glob.glob1(self.download_parts_dir, '*[0-9]-*[0-9].csv')]
        if not parts:
            return
        parts.sort()
        last_start, last_next = parts[-1]
        if last_next == 0 and last_start != 0:
            self.is_finished_parts = True
        else:
            self.start_value = last_next + 1
        failed_gaps = self._find_gaps(parts)
        if failed_gaps:
            print('+++ Discovering failed parts for this gaps: {}'.format(failed_gaps))
        for s, e in failed_gaps:
            p = self._scrap_total_page(s, e)
            if p <= self.pages_per_part + self.pages_delta:
                self.failed_parts.append((s, e))
            else:
                while s < e:
                    n = self.discover_best_actual_value(s)
                    if n is None or n > e:
                        n = e
                    print('!!! Discovered failed part: [{} - {}]'.format(s, n))
                    self.failed_parts.append((s, n))
                    s = n + 1

    def _handle(self, *args, **options):
        self.init_vars(*args, **options)
        if options.get('merge'):
            return self.merge_parts()
        if options.get('show_failed_parts'):
            return self.show_failed_parts()
        if options.get('clean'):
            shutil.rmtree(self.download_parts_dir)

        if os.path.exists(self.download_parts_dir):
            if glob.glob1(self.download_parts_dir, '*[0-9]-*[0-9].csv') and not self.noinput:
                confirm = input('previous download parts already exists! do you want to continue previous or restart?'
                                '([C]Countine / [r]Restart) ')
                if (confirm.lower() or 'c') == 'r':
                    shutil.rmtree(self.download_parts_dir)
                    os.makedirs(self.download_parts_dir)
        else:
            os.makedirs(self.download_parts_dir)
        print('++ Scrapping Total Pages ... ==> ', end='')
        pages_info = self._scrap_total_page(0, None, include_extra=True)
        self.total_page = pages_info['pages']
        self.records_per_page = pages_info['records_per_page']
        print('OK')
        self.pages_per_part = int(math.ceil(self.total_page / self.parts))
        print('++ Distributing [{}] pages between [{}] parts ...'.format(self.total_page, self.parts))
        print('++ [pages_per_part = {}] [records_per_page = {}]'.format(self.pages_per_part, self.records_per_page))
        print('++ Initializing Resume vars ...')
        self.init_resume_vars()
        if self.failed_parts:
            print('!!! discovered this failed parts from previous: {}'.format(self.failed_parts))
        start_value = self.start_value
        while not self.is_finished_parts:
            print('++ Discovering best actual value from [{}] ...'.format(start_value))
            t1 = timezone.now()
            next_value = self.discover_best_actual_value(start_value)
            duration = (timezone.now() - t1).total_seconds()
            print('++ Discovered [{}] for [{}] in [{}] Seconds'.format(next_value, start_value, duration))
            self.download_range_data(start_value, next_value)
            print('*********** Finished = {} **************'.format(self._finished_counter))
            if next_value is None:
                break
            print('!!! waiting for [{}] seconds ...'.format(self.round_wait_seconds))
            time.sleep(self.round_wait_seconds)
            start_value = next_value + 1

        print('+++ download parts finished. ')
        print('+++ Retrying failed parts ....')
        self.retry_failed_parts()
        if self.failed_parts:
            print('!!!!!!! We already failed this parts: {}'.format(self.failed_parts))
        print('########## Finished downloads ###########')

    def merge_parts(self):
        if not os.path.exists(self.download_parts_dir):
            print('!!! Cannot merge files! part files not downloaded yet!')
            return
        files = glob.glob1(self.download_parts_dir, '*[0-9]-*[0-9].csv')
        if not files:
            print('!!! Cannot merge files! parts files not downloaded yet!')
            return
        if os.path.exists(self.export_file_path) and not self.noinput:
            confirm = input(
                '!!! Export file ({}) already exists!\nDo you want to replace?(N/y) '.format(self.export_file_path))
            if (confirm.lower() or 'n') == 'n':
                return
        parts = [tuple(map(int, f[:-4].split('-'))) for f in files]
        parts.sort()
        gaps = self._find_gaps(parts)
        failed = False
        if parts[-1][1] != 0 or gaps:
            print('!!! Seems downloads parts was not completed!!!')
            failed = True
        if gaps:
            print('!!! This parts was not downloaded yet: {}'.format(gaps))
            failed = True
        if failed and not self.noinput:
            confirm = input('Do you want to continue merge?(N/y) ')
            if (confirm.lower() or 'n') == 'n':
                return
        print('+++ Merging [{}] files ...'.format(len(files)))
        with open(self.export_file_path, 'wb') as export_file:
            included_header = False
            for s, e in parts:
                file_path = os.path.join(self.download_parts_dir, '{}-{}.csv'.format(s, e))
                with open(file_path, 'rb') as fin:
                    header = next(fin)  # skip header
                    if not included_header:
                        export_file.write(header)
                        included_header = True
                    export_file.write(fin.read())
        print('***** Merged to: [{}]'.format(self.export_file_path))

    def show_failed_parts(self):
        if not os.path.exists(self.download_parts_dir):
            print('!!! No parts downloaded yet!')
            return
        files = glob.glob1(self.download_parts_dir, '*[0-9]-*[0-9].csv')
        if not files:
            print('!!! No parts downloaded yet!')
            return
        parts = [tuple(map(int, f[:-4].split('-'))) for f in files]
        parts.sort()
        gaps = self._find_gaps(parts)
        failed = False
        if parts[-1][1] != 0 or gaps:
            print('!!! Seems downloads parts was not completed yet!!!')
            print('++ records from [{}] to [{}] value is downloaded.'.format(parts[0][0], parts[-1][1]))
            failed = True
        if gaps:
            print('!!! This parts was not downloaded yet: {}'.format(gaps))
            failed = True
        if not failed:
            print('All parts downloaded successfully for [{}] county.'.format(self.county))

    def retry_failed_parts(self):
        max_retry = 3
        while self.failed_parts and max_retry > 0:
            for start_value, end_value in self.failed_parts[:]:
                self.failed_parts.pop(0)
                print('++++ retrying failed part {} - {} ...'.format(start_value, end_value))
                self.download_range_data(start_value, end_value)
                print('!!! waiting for [{}] seconds ...'.format(self.round_wait_seconds))
                time.sleep(self.round_wait_seconds)
            max_retry -= 1

    @retry(wait_exponential_multiplier=10000, wait_exponential_max=60000, stop_max_attempt_number=10)
    def discover_best_actual_value(self, start_value):
        lower_bound = start_value
        upper_bound = 2 * start_value + 1
        max_upper_bound = None
        p = 0
        rnd = 0
        while True:
            if upper_bound == lower_bound:
                return max_upper_bound or upper_bound

            prev_p = p
            p = self._scrap_total_page(start_value, upper_bound)
            rnd += 1
            print('$$$ Round=[{}]: start_value=[{}], upper_bound=[{}], pages=[{}]'.format(rnd, start_value,
                                                                                          upper_bound, p))
            if (max_upper_bound is None) and (p == prev_p) and \
                (p + self._scrap_total_page(upper_bound, None) <= self.pages_per_part + self.pages_delta):
                    return None

            if 0 <= p - self.pages_per_part <= self.pages_delta:
                return upper_bound
            if p < self.pages_per_part:
                if max_upper_bound is None:
                    lower_bound, upper_bound = upper_bound, 2 * upper_bound
                else:
                    lower_bound = upper_bound
                    upper_bound = upper_bound + (max_upper_bound - upper_bound) // 2
            if p > self.pages_per_part:
                max_upper_bound = upper_bound
                upper_bound = lower_bound + (upper_bound - lower_bound) // 2

    def download_range_data(self, start_value, end_value):
        try:
            self._download_range_data(start_value, end_value)
        except KeyboardInterrupt:
            print('Canceled!')
            sys.exit(1)
        except Exception:
            self.failed_parts.append((start_value, end_value))
            print('!!! Unexpected Exception for download range [{} - {}]'.format(start_value, end_value))
            traceback.print_exc()
        finally:
            self._finished_counter += 1

    def _download_range_data(self, start_value, end_value):
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
            if re.search(self.county_conf['generating_report_pattern'], check_result):
                time.sleep(self.check_report_interval)
                continue
            bs = BeautifulSoup(check_result, 'html.parser')
            a = bs.find('a')
            if not a:
                print('!!! {}: Not found Download link in content: {}'.format(range_str, check_result))
                raise Exception('Not found Download link')
            print('+++ {}: Downloading Report ...'.format(range_str))
            download_endpoint = a.get('href')
            download_base = urljoin(self.base_url, self.county_conf['eagle_web_url'])
            download_url = urljoin(download_base, download_endpoint)
            destfile = os.path.join(self.download_parts_dir, '{}-{}.csv'.format(start_value, end_value or 0))
            self._download_file(session, download_url, destfile)
            break
        end_time = timezone.now()
        duration = (end_time - start_time).total_seconds()
        print('+++ {}: Finished at [{}] - Duration={} Seconds!'.format(range_str, end_time, duration))

    def _download_file(self, session, url, destfile):
        r = session.get(url, stream=True)
        if r.status_code == 200:
            with open(destfile, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        else:
            raise Exception('Cannot Download File {}, to be saved in {}'.format(url, destfile))

    def _scrap_total_page(self, start_value, end_value, session=None, include_extra=False):
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
        pagination_title = bs.find(id='middle').find(text=re.compile(self.county_conf['pagination_re']))
        if not pagination_title:
            raise Exception('!!! {}: Cannot scrap pagination title'.format(range_str))
        total_records = re.findall(self.county_conf['total_records_re1'], pagination_title)
        records_per_page = len(bs.findAll("tr", {"class": "tableRow1"})) + \
                           len(bs.findAll("tr", {"class": "tableRow2"}))
        if total_records:
            pages = [int(math.ceil(int(total_records[0]) / (self.records_per_page or records_per_page)))]
        else:
            pages = re.findall(self.county_conf['total_pages_re'], pagination_title)
        if not pages:
            raise Exception('!!! {}: Cannot scrap total pages'.format(range_str))
        if include_extra:
            return dict(pages=int(pages[0]), records_per_page=records_per_page)
        return int(pages[0])

