from Cryptodome.Cipher import AES

import pubnub
from pubnub.pnconfiguration import PNConfiguration


def test_x():
    assert 1 + 1 == 2
    assert PNConfiguration.ALLOWED_AES_MODES == [AES.MODE_CBC, AES.MODE_GCM]
