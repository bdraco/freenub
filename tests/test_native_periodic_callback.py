"""`NativePeriodicCallback` schedules its recurring timer as a daemon thread.

`start()` used to raise `AttributeError` because `_schedule_next` set `daemon`
on an attribute (`_timer`) the class never defines. That error propagated out of
`subscribe().execute()` and left a live subscription without a recurring
heartbeat.
"""

import threading

from pubnub.pubnub import NativePeriodicCallback


def test_start_schedules_a_daemon_timer_and_fires_the_callback():
    fired = threading.Event()
    periodic = NativePeriodicCallback(fired.set, 0.01)

    periodic.start()
    try:
        assert periodic._timeout is not None
        assert periodic._timeout.daemon is True
        assert fired.wait(timeout=2)
    finally:
        periodic.stop()


def test_stop_cancels_the_pending_timer():
    periodic = NativePeriodicCallback(lambda: None, 60)

    periodic.start()
    timer = periodic._timeout
    periodic.stop()

    assert periodic._timeout is None
    assert timer is not None
    assert timer.finished.is_set()
