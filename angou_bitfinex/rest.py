from urllib.parse import urlparse
import base64
import logging
import requests
from . import auth_utils


LOGGER = logging.getLogger(__name__)


_BASE_URL = 'https://api.bitfinex.com'


class _BitfinexV1Auth(requests.auth.AuthBase):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def __call__(self, r):
        body = r.body or ''
        if not isinstance(body, (bytes, bytearray)):
            body = body.encode('utf8')

        payload = base64.b64encode(body)

        r.headers.update({
            'X-BFX-APIKEY': self.api_key,
            'X-BFX-PAYLOAD': payload,
            'X-BFX-SIGNATURE': auth_utils.generate_signature(self.api_secret, payload),
        })

        return r


class _BitfinexV2Auth(requests.auth.AuthBase):
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def __call__(self, r):
        path = urlparse(r.url).path

        body = r.body or ''
        if not isinstance(body, str):
            body = body.decode('utf8')

        nonce = auth_utils.generate_nonce()

        r.headers.update({
            'bfx-nonce': nonce,
            'bfx-apikey': self.api_key,
            'bfx-signature': auth_utils.generate_signature(self.api_secret,
                                                           f'/api{path}{nonce}{body}'),
        })

        return r


class InvalidJSON(Exception):
    pass


class RestV1Error(Exception):
    pass


class RestV2Error(Exception):
    def __init__(self, code, message):
        super().__init__(f'[{code}] {message}')
        self.code = code
        self.message = message


class RestV1Session:
    def __init__(self, api_key, api_secret, timeout=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        self._auth = _BitfinexV1Auth(api_key, api_secret)

    @staticmethod
    def _postprocess(r):
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                err_obj = r.json()
            except ValueError:
                pass
            else:
                try:
                    raise RestV1Error(err_obj['message'])
                except KeyError:
                    pass
            raise
        else:
            try:
                return r.json()
            except ValueError:
                raise InvalidJSON()

    def call_public(self, method, params=None):
        LOGGER.debug('GET %s %s', method, params)
        return self._postprocess(self._session.request(
            'GET', f'{_BASE_URL}/v1/{method}', params=params, timeout=self.timeout))

    def call_auth(self, method, params=None):
        LOGGER.debug('POST %s %s', method, params)

        path = f'/v1/{method}'

        params = params or {}
        params.update({
            'request': path,
            'nonce': auth_utils.generate_nonce(),
        })

        return self._postprocess(self._session.request(
            'POST', f'{_BASE_URL}{path}', json=params, auth=self._auth, timeout=self.timeout))


class RestV2Session:
    def __init__(self, api_key, api_secret, timeout=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        })
        self._auth = _BitfinexV2Auth(api_key, api_secret)

    @staticmethod
    def _postprocess(r):
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            try:
                err_obj = r.json()
            except ValueError:
                pass
            else:
                if isinstance(err_obj, list) and len(err_obj) >= 3:
                    raise RestV2Error(err_obj[1], err_obj[2])
            raise
        else:
            try:
                return r.json()
            except ValueError:
                raise InvalidJSON()

    def call_public(self, method, params=None):
        LOGGER.debug('GET %s %s', method, params)
        return self._postprocess(self._session.request(
            'GET', f'{_BASE_URL}/v2/{method}', params=params, timeout=self.timeout))

    def call_auth(self, method, params=None):
        LOGGER.debug('POST %s %s', method, params)
        return self._postprocess(self._session.request(
            'POST', f'{_BASE_URL}/v2/{method}', json=params, auth=self._auth, timeout=self.timeout))
