import json
import requests
from urllib.parse import urlparse, parse_qsl, urlencode


class RestResponseException(Exception):
    def __init__(self, status_code, reason, response):
        self.args = status_code, reason, response.json()
        self.status_code = status_code
        self.reason = reason
        self.response = response


class RestClient(object):

    headers = {'content-type': 'application/json'}
    auth_token_endpoint = '/token/auth/'

    def __init__(self, server_url, username=None, password=None):
        self.server_url = server_url.rstrip()
        self._api_key = None
        self.username = username
        self.password = password

    @staticmethod
    def get_json(response):
        if response.ok:
            return response.json()
        raise RestResponseException(
            response.status_code, response.reason, response)

    @property
    def api_key(self):
        if not self._api_key:
            data = {'username': self.username, 'password': self.password}
            r = self.post(self.auth_token_endpoint, data=data, auth=False)
            self._api_key = r['token']
        return self._api_key

    def abs_url(self, endpoint):
        return '{0}/{1}'.format(self.server_url.rstrip('/'),
                                endpoint.lstrip('/'))

    def make_headers(self, extra_headers=None, auth=True):
        headers = self.headers.copy()
        if auth:
            token = 'Codata %s' % self.api_key
            headers.update({'Authorization': token})
        headers.update(extra_headers or {})
        return headers

    def post(self, path, data=None, files=None, headers=None, auth=True,
             raw_response=False, **kwargs):
        headers = self.make_headers(extra_headers=headers, auth=auth)
        is_json = 'application/json' in (headers.get('content-type') or '')
        data = json.dumps(data) if is_json else (data or {})
        res = requests.post(self.abs_url(path), data=data, files=files,
                            headers=headers, **kwargs)
        if not raw_response:
            res = self.get_json(res)
        return res

    def delete(self, path, data=None, headers=None, auth=True,
               raw_response=False, **kwargs):
        headers = self.make_headers(extra_headers=headers, auth=auth)
        is_json = 'application/json' in (headers.get('content-type') or '')
        data = json.dumps(data) if is_json else (data or '')
        res = requests.delete(self.abs_url(path), data=data,
                              headers=headers, **kwargs)
        if not raw_response:
            res = self.get_json(res)
        return res

    def put(self, path, data=None, files=None, headers=None, auth=True,
            raw_response=False, **kwargs):
        headers = self.make_headers(extra_headers=headers, auth=auth)
        is_json = 'application/json' in (headers.get('content-type') or '')
        data = json.dumps(data) if is_json else (data or '')
        res = requests.put(self.abs_url(path), data=data, files=files,
                           headers=headers, **kwargs)
        if not raw_response:
            res = self.get_json(res)
        return res

    def get(self, path, params=None, headers=None, auth=True,
            raw_response=False, **kwargs):
        params = params or {}
        url_parts = urlparse(path)
        path = url_parts.path
        query = dict(parse_qsl(url_parts.query))
        query.update(params)
        params = urlencode(query)

        headers = self.make_headers(extra_headers=headers, auth=auth)
        res = requests.get(self.abs_url(path), headers=headers,
                           params=params, **kwargs)
        if not raw_response:
            res = self.get_json(res)
        return res


if __name__ == '__main__':
    api_url = 'http://35.164.55.7:81/'
    username = '<USERNAME>'
    password = '<PASS>'
    client = RestClient(api_url, username, password)
    client.get('grand/api/v1/property')
