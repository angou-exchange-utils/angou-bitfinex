import json
import base64
import requests
import auth_utils


_BASE_URL = 'https://api.bitfinex.com'


class RestV1Error(Exception):
    pass


class RestV2Error(Exception):
    def __init__(self, code, message):
        super().__init__(f'[{code}] {message}')
        self.code = code
        self.message = message


class RestV1Client:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    @staticmethod
    def _postprocess(req):
        try:
            req.raise_for_status()
        except requests.exceptions.HTTPError:
            raise RestV1Error(req.json()['message'])
        else:
            return req.json()

    def call_public(self, method, **kwargs):
        return self._postprocess(requests.get(f'{_BASE_URL}/v1/{method}', params=kwargs))

    def call_auth(self, method, **kwargs):
        nonce = auth_utils.generate_nonce()
        path = f'/v1/{method}'

        post_data = kwargs
        post_data['request'] = path
        post_data['nonce'] = nonce

        post_data_json = json.dumps(post_data)
        payload = base64.b64encode(post_data_json.encode('utf8'))
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-BFX-APIKEY': self.api_key,
            'X-BFX-PAYLOAD': payload,
            'X-BFX-SIGNATURE': auth_utils.generate_signature(self.api_secret, payload),
        }

        return self._postprocess(
            requests.post(f'{_BASE_URL}{path}', data=post_data_json, headers=headers))


class RestV2Client:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    @staticmethod
    def _postprocess(req):
        try:
            req.raise_for_status()
        except requests.exceptions.HTTPError:
            _, code, message = req.json()
            raise RestV2Error(code, message)
        else:
            return req.json()

    def call_public(self, method, **kwargs):
        return self._postprocess(requests.get(f'{_BASE_URL}/v2/{method}', params=kwargs))

    def call_auth(self, method, **kwargs):
        nonce = auth_utils.generate_nonce()
        path = f'/v2/{method}'
        post_data_json = json.dumps(kwargs)
        signature = auth_utils.generate_signature(
            self.api_secret, f'/api{path}{nonce}{post_data_json}')

        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'bfx-nonce': nonce,
            'bfx-apikey': self.api_key,
            'bfx-signature': signature,
        }

        return self._postprocess(
            requests.post(f'{_BASE_URL}{path}', data=post_data_json, headers=headers))
