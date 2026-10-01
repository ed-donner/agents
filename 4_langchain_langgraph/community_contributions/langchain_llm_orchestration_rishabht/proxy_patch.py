import ssl
import warnings

import httpx
import requests
import urllib3


def _patch_httpx_ssl():
    _original_client_init = httpx.Client.__init__
    _original_async_client_init = httpx.AsyncClient.__init__
    _original_transport_init = httpx.HTTPTransport.__init__
    _original_async_transport_init = httpx.AsyncHTTPTransport.__init__

    def _new_client_init(self, *args, **kwargs):
        kwargs["verify"] = False
        _original_client_init(self, *args, **kwargs)

    def _new_async_client_init(self, *args, **kwargs):
        kwargs["verify"] = False
        _original_async_client_init(self, *args, **kwargs)

    def _new_transport_init(self, *args, **kwargs):
        kwargs["verify"] = False
        _original_transport_init(self, *args, **kwargs)

    def _new_async_transport_init(self, *args, **kwargs):
        kwargs["verify"] = False
        _original_async_transport_init(self, *args, **kwargs)

    httpx.Client.__init__ = _new_client_init
    httpx.AsyncClient.__init__ = _new_async_client_init
    httpx.HTTPTransport.__init__ = _new_transport_init
    httpx.AsyncHTTPTransport.__init__ = _new_async_transport_init

    ssl._create_default_https_context = ssl._create_unverified_context
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    warnings.filterwarnings("ignore", category=Warning, module="httpx")


def _patch_requests_ssl():
    _original_request = requests.Session.request

    def _new_request(self, method, url, **kwargs):
        kwargs["verify"] = False
        return _original_request(self, method, url, **kwargs)

    requests.Session.request = _new_request
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


_patch_httpx_ssl()
_patch_requests_ssl()
