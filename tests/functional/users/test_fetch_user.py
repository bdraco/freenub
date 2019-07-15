import pytest

from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.endpoints.users.fetch_user import FetchUser
from pubnub.exceptions import PubNubException


SUB_KEY = 'sub'
AUTH = 'auth'


def test_fetch_user():
    config = PNConfiguration()
    config.subscribe_key = SUB_KEY
    config.auth_key = AUTH
    user = PubNub(config).fetch_user()
    user.include(['a', 'b'])
    with pytest.raises(PubNubException):
        user.build_path()

    user.user_id('foo')
    assert user.build_path() == FetchUser.FETCH_USER_PATH % (SUB_KEY, 'foo')

    params = user.custom_params()
    assert params['include'] == '%5B%22a%22%2C%20%22b%22%5D'
    assert AUTH == user.build_params_callback()({})['auth']
