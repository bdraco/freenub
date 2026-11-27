"""`PNConfiguration` must reject a non-positive heartbeat interval.

`AsyncioPeriodicCallback._schedule_next` converts `heartbeat_interval` to
seconds and divides the elapsed time by it, so an interval of zero raises
`ZeroDivisionError` from inside `subscribe().execute()` (reachable through
`reconnect()` -> `_register_heartbeat_timer()` -> `start()`). A negative
interval does not raise: every pass moves `_next_timeout` further into the
past, so `call_at` is always handed a time that has already passed and the
heartbeat fires continuously.

Neither value has to be typed by the caller. `set_presence_timeout` derives
the interval as `(timeout / 2) - 1`, so `set_presence_timeout(2)` asks for
exactly `0.0` and `set_presence_timeout(1)` asks for `-0.5`.
"""

import pytest

from pubnub.pnconfiguration import PNConfiguration


@pytest.mark.parametrize("timeout", [1, 2])
def test_set_presence_timeout_rejects_non_positive_derived_interval(timeout):
    """The public timeout setter is the path that reaches the bad values."""
    config = PNConfiguration()

    with pytest.raises(ValueError, match="heartbeat_interval"):
        config.set_presence_timeout(timeout)


def test_rejected_timeout_leaves_the_configuration_untouched():
    """A rejected call must not leave a half-applied configuration behind."""
    config = PNConfiguration()

    with pytest.raises(ValueError, match="heartbeat_interval"):
        config.set_presence_timeout(2)

    assert config.presence_timeout == PNConfiguration.DEFAULT_PRESENCE_TIMEOUT
    assert config.heartbeat_interval == PNConfiguration.DEFAULT_HEARTBEAT_INTERVAL
    assert config.heartbeat_default_values is True


@pytest.mark.parametrize("interval", [0, 0.0, -0.5, -1])
def test_custom_interval_rejects_non_positive_values(interval):
    config = PNConfiguration()

    with pytest.raises(ValueError, match="heartbeat_interval"):
        config.set_presence_timeout_with_custom_interval(20, interval)


def test_custom_interval_still_accepts_positive_values():
    config = PNConfiguration()

    config.set_presence_timeout_with_custom_interval(20, 0.1)

    assert config.presence_timeout == 20
    assert config.heartbeat_interval == 0.1


def test_smallest_positive_derived_interval_is_accepted():
    """`set_presence_timeout(3)` is the first timeout that derives > 0."""
    config = PNConfiguration()

    config.set_presence_timeout(3)

    assert config.presence_timeout == 3
    assert config.heartbeat_interval == 0.5
