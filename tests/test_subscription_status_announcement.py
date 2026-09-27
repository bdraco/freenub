"""Connection status announcement across reconnect().

`SubscriptionManager._subscription_status_announced` is a one-shot latch that
guards the only place `PNConnectedCategory` is announced. `reconnect()` must
clear it, otherwise a caller that reconnects gets a working subscribe loop and
no further connection status for the lifetime of the manager.

`reconnect()` also doubles as the internal restart primitive for
`adapt_unsubscribe_builder` and `adapt_state_builder`. Those pass
`announce_status=False`, so a partial unsubscribe or a `set_state()` restarts
the loop without reporting a connection that never dropped.

Both managers are driven through a stubbed `Subscribe` endpoint so no network
traffic is involved.
"""

import asyncio

import pytest
import pytest_asyncio

import pubnub.pubnub as pubnub_native
import pubnub.pubnub_asyncio as pubnub_asyncio
from pubnub.callbacks import SubscribeCallback
from pubnub.dtos import UnsubscribeOperation
from pubnub.enums import PNStatusCategory
from pubnub.errors import PNERR_REQUEST_CANCELLED
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.pubnub_asyncio import (
    AsyncioEnvelope,
    PubNubAsyncio,
    PubNubAsyncioException,
)

CHANNEL = "test-channel"
OTHER_CHANNEL = "other-channel"

# Time for the asyncio subscribe loop to restart itself, where there is no
# response to key off. Every await in that path is on an already-resolved
# future. Response delivery is signalled rather than timed; see `async_client`.
SETTLE = 0.05


def make_config():
    config = PNConfiguration()
    config.subscribe_key = "test-sub-key"
    config.publish_key = "test-pub-key"
    config.uuid = "test-uuid"
    # Keeps the leave request off the unsubscribe path; this suite never
    # exercises the network.
    config.suppress_leave_events = True
    return config


def empty_subscribe_payload(timetoken=1000):
    """The shape `SubscribeEnvelope.from_json` expects, with no messages."""
    return {"t": {"t": str(timetoken), "r": 1}, "m": []}


def success_status():
    status = PNStatus()
    status.error = False
    status.category = PNStatusCategory.PNAcknowledgmentCategory
    return status


def cancelled_status():
    status = PNStatus()
    status.error = True
    status.category = PNStatusCategory.PNCancelledCategory
    status.error_data = PubNubException(pn_error=PNERR_REQUEST_CANCELLED)
    return status


class StatusRecorder(SubscribeCallback):
    def __init__(self):
        self.categories = []

    def status(self, pubnub, status):
        self.categories.append(status.category)

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass


class AsyncioSubscribeStub:
    """Stands in for `Subscribe` on the asyncio path.

    `future()` parks on a queue until a test hands it a response, which is what
    a real long poll does. Cancellation is translated into a
    `PNCancelledCategory` envelope the way `PubNubAsyncio.request_future` does.
    """

    queue = None
    request_count = 0

    def __init__(self, pubnub):
        self._pubnub = pubnub

    def channels(self, channels):
        return self

    def channel_groups(self, groups):
        return self

    def timetoken(self, timetoken):
        return self

    def region(self, region):
        return self

    def filter_expression(self, expression):
        return self

    async def future(self):
        type(self).request_count += 1
        try:
            return await type(self).queue.get()
        except asyncio.CancelledError:
            return PubNubAsyncioException(result=None, status=cancelled_status())


@pytest_asyncio.fixture
async def asyncio_subscribe(monkeypatch):
    # Async so the queue is built inside the running loop. On Python 3.9
    # `asyncio.Queue()` binds `get_event_loop()` at construction, and a queue
    # built from a sync fixture belongs to a different loop than the test, so
    # `queue.get()` awaits a foreign future and raises.
    AsyncioSubscribeStub.queue = asyncio.Queue()
    AsyncioSubscribeStub.request_count = 0
    monkeypatch.setattr(pubnub_asyncio, "Subscribe", AsyncioSubscribeStub)
    return AsyncioSubscribeStub


@pytest_asyncio.fixture
async def async_client(asyncio_subscribe):
    pubnub = PubNubAsyncio(make_config())
    recorder = StatusRecorder()
    pubnub.add_listener(recorder)

    # Every assertion in this suite is about what the manager did with a
    # response, so the stub signals from the manager side: an event set when
    # the subscribe stub picks a response off the queue would fire before
    # `_handle_endpoint_call` had announced anything.
    manager = pubnub._subscription_manager
    handled = asyncio.Event()
    handle_endpoint_call = manager._handle_endpoint_call

    def signal_when_handled(raw_result, status):
        handle_endpoint_call(raw_result, status)
        handled.set()

    manager._handle_endpoint_call = signal_when_handled
    asyncio_subscribe.handled = handled

    try:
        yield pubnub, recorder, asyncio_subscribe
    finally:
        await pubnub.stop()
        # `stop()` cancels only the newest loop task; let the superseded ones
        # see their cancellation before the loop closes under them.
        await asyncio.sleep(0)


async def deliver_subscribe_response(stub, timetoken=1000):
    """Hand the parked subscribe loop one successful response.

    Returns once the manager has finished with it, so a missed wake-up fails as
    a timeout rather than as a wrong-categories assertion.
    """
    stub.handled.clear()
    stub.queue.put_nowait(
        AsyncioEnvelope(
            result=empty_subscribe_payload(timetoken), status=success_status()
        )
    )
    await asyncio.wait_for(stub.handled.wait(), timeout=2)


class NativeCallStub:
    """The handle `NativeSubscriptionManager._stop_subscribe_loop` inspects."""

    def __init__(self):
        self.is_executed = False
        self.is_canceled = False

    def cancel(self):
        self.is_canceled = True


class NativeSubscribeStub:
    """Stands in for `Subscribe` on the native path.

    `pn_async` is non-blocking on the real endpoint: it hands the request to a
    worker and returns. The stub records the callback instead of firing it, so
    a test decides when the long poll answers, on the calling thread.
    """

    pending = None
    request_count = 0

    def __init__(self, pubnub):
        self._pubnub = pubnub

    def channels(self, channels):
        return self

    def channel_groups(self, groups):
        return self

    def timetoken(self, timetoken):
        return self

    def region(self, region):
        return self

    def filter_expression(self, expression):
        return self

    def pn_async(self, callback):
        type(self).request_count += 1
        call = NativeCallStub()
        type(self).pending.append((call, callback))
        return call


@pytest.fixture
def native_subscribe(monkeypatch):
    NativeSubscribeStub.pending = []
    NativeSubscribeStub.request_count = 0
    monkeypatch.setattr(pubnub_native, "Subscribe", NativeSubscribeStub)
    return NativeSubscribeStub


@pytest.fixture
def native_client(native_subscribe):
    pubnub = PubNub(make_config())
    recorder = StatusRecorder()
    pubnub.add_listener(recorder)
    try:
        yield pubnub, recorder, native_subscribe
    finally:
        pubnub._subscription_manager.stop()


def deliver_native_response(stub, timetoken=1000):
    """Answer the outstanding subscribe call with a successful response."""
    call, callback = stub.pending.pop()
    # Anything still queued behind it was superseded by a restart of the loop.
    stub.pending.clear()
    call.is_executed = True
    callback(empty_subscribe_payload(timetoken), success_status())


# --- asyncio manager ----------------------------------------------------


@pytest.mark.asyncio
async def test_subscribe_announces_connected_once(async_client):
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub)

    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]


@pytest.mark.asyncio
async def test_connected_not_repeated_per_subscribe_response(async_client):
    """The latch still suppresses one announcement per long-poll iteration."""
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)
    await deliver_subscribe_response(stub, timetoken=1001)
    await deliver_subscribe_response(stub, timetoken=1002)

    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]


@pytest.mark.asyncio
async def test_reconnect_announces_connected_again(async_client):
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)
    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]

    pubnub.reconnect()
    await asyncio.sleep(SETTLE)

    # Nothing is announced at the moment reconnect() is called; the status
    # rides on the first successful subscribe response after it.
    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]

    await deliver_subscribe_response(stub, timetoken=1001)

    assert recorder.categories == [
        PNStatusCategory.PNConnectedCategory,
        PNStatusCategory.PNConnectedCategory,
    ]


@pytest.mark.asyncio
async def test_reconnect_announces_connected_once_not_per_iteration(async_client):
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)

    pubnub.reconnect()
    await asyncio.sleep(SETTLE)
    await deliver_subscribe_response(stub, timetoken=1001)
    await deliver_subscribe_response(stub, timetoken=1002)
    await deliver_subscribe_response(stub, timetoken=1003)

    assert recorder.categories == [
        PNStatusCategory.PNConnectedCategory,
        PNStatusCategory.PNConnectedCategory,
    ]


@pytest.mark.asyncio
async def test_disconnect_reconnect_cycle_announces_connected(async_client):
    """`disconnect()` / `reconnect()` is the cycle that produced no events."""
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)

    pubnub._subscription_manager.disconnect()
    await asyncio.sleep(SETTLE)
    pubnub._subscription_manager.reconnect()
    await asyncio.sleep(SETTLE)
    await deliver_subscribe_response(stub, timetoken=1001)

    assert recorder.categories == [
        PNStatusCategory.PNConnectedCategory,
        PNStatusCategory.PNConnectedCategory,
    ]


@pytest.mark.asyncio
async def test_on_reconnect_announces_reconnected_without_duplicate(async_client):
    """`on_reconnect` suppresses the connected status in favour of its own.

    It sets the latch back to True straight after calling `reconnect()`, which
    is dead code unless `reconnect()` clears it. With the reset in place that
    assignment becomes load-bearing: the reconnection path must still announce
    `PNReconnectedCategory` alone.
    """
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)
    recorder.categories.clear()

    pubnub._subscription_manager._reconnection_listener.on_reconnect()
    await asyncio.sleep(SETTLE)
    await deliver_subscribe_response(stub, timetoken=1001)

    assert recorder.categories == [PNStatusCategory.PNReconnectedCategory]


@pytest.mark.asyncio
async def test_partial_unsubscribe_announces_nothing(async_client):
    """`adapt_unsubscribe_builder` restarts the loop without re-announcing.

    Dropping one of two channels leaves a live subscription. The channels that
    remain were already connected, so there is no new subscription to report.
    """
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL, OTHER_CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)
    recorder.categories.clear()

    pubnub._subscription_manager.adapt_unsubscribe_builder(
        UnsubscribeOperation(channels=[OTHER_CHANNEL], channel_groups=[])
    )
    await asyncio.sleep(SETTLE)
    await deliver_subscribe_response(stub, timetoken=1001)

    assert recorder.categories == []


@pytest.mark.asyncio
async def test_unsubscribe_all_then_subscribe_announces_connected(async_client):
    """A full unsubscribe drops the subscription, so the next one is new.

    `adapt_unsubscribe_builder` passes `announce_status=False` and
    `_start_subscribe_loop` returns early with no channels, so the latch is
    left set. Only the `reconnect()` on the subscribe path clears it again.
    """
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)
    pubnub.unsubscribe_all()
    await asyncio.sleep(SETTLE)
    recorder.categories.clear()

    pubnub.subscribe().channels([OTHER_CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1001)

    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]


@pytest.mark.asyncio
async def test_set_state_announces_nothing(async_client):
    """`SetState.custom_params` calls `adapt_state_builder` on every request.

    Writing presence state is not a connection event, so the restart it
    triggers must not re-announce.
    """
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)
    recorder.categories.clear()

    pubnub.set_state().channels([CHANNEL]).state({"mood": "ok"}).custom_params()
    await asyncio.sleep(SETTLE)
    await deliver_subscribe_response(stub, timetoken=1001)

    assert recorder.categories == []


@pytest.mark.asyncio
async def test_reconnect_restarts_the_subscribe_loop(async_client):
    """The loop the status is meant to describe really does restart."""
    pubnub, recorder, stub = async_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    await deliver_subscribe_response(stub, timetoken=1000)
    before = stub.request_count

    pubnub.reconnect()
    await asyncio.sleep(SETTLE)

    assert stub.request_count > before


# --- native manager -----------------------------------------------------


def test_native_subscribe_announces_connected_once(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub)

    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]


def test_native_connected_not_repeated_per_subscribe_response(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    deliver_native_response(stub, timetoken=1001)
    deliver_native_response(stub, timetoken=1002)

    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]


def test_native_reconnect_announces_connected_again(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]

    pubnub.reconnect()
    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]

    deliver_native_response(stub, timetoken=1001)

    assert recorder.categories == [
        PNStatusCategory.PNConnectedCategory,
        PNStatusCategory.PNConnectedCategory,
    ]


def test_native_reconnect_announces_connected_once_not_per_iteration(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)

    pubnub.reconnect()
    deliver_native_response(stub, timetoken=1001)
    deliver_native_response(stub, timetoken=1002)
    deliver_native_response(stub, timetoken=1003)

    assert recorder.categories == [
        PNStatusCategory.PNConnectedCategory,
        PNStatusCategory.PNConnectedCategory,
    ]


def test_native_disconnect_reconnect_cycle_announces_connected(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)

    pubnub._subscription_manager.disconnect()
    pubnub._subscription_manager.reconnect()
    deliver_native_response(stub, timetoken=1001)

    assert recorder.categories == [
        PNStatusCategory.PNConnectedCategory,
        PNStatusCategory.PNConnectedCategory,
    ]


def test_native_on_reconnect_announces_reconnected_without_duplicate(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    recorder.categories.clear()

    pubnub._subscription_manager._reconnection_listener.on_reconnect()
    deliver_native_response(stub, timetoken=1001)

    assert recorder.categories == [PNStatusCategory.PNReconnectedCategory]


class SynchronousNativeSubscribeStub(NativeSubscribeStub):
    """Answers one subscribe call on the calling thread.

    The real handler answers on a worker thread
    (`request_handlers/requests_handler.py:113`), so a response can land while
    the caller of `reconnect()` is still running. This stub makes that ordering
    reachable without depending on thread timing.
    """

    answer_synchronously = False

    def pn_async(self, callback):
        if not type(self).answer_synchronously:
            return super().pn_async(callback)

        type(self).answer_synchronously = False
        type(self).request_count += 1
        call = NativeCallStub()
        call.is_executed = True
        callback(empty_subscribe_payload(), success_status())
        return call


@pytest.fixture
def synchronous_native_client(monkeypatch):
    SynchronousNativeSubscribeStub.pending = []
    SynchronousNativeSubscribeStub.request_count = 0
    SynchronousNativeSubscribeStub.answer_synchronously = False
    monkeypatch.setattr(pubnub_native, "Subscribe", SynchronousNativeSubscribeStub)

    pubnub = PubNub(make_config())
    recorder = StatusRecorder()
    pubnub.add_listener(recorder)
    try:
        yield pubnub, recorder, SynchronousNativeSubscribeStub
    finally:
        pubnub._subscription_manager.stop()


def test_native_on_reconnect_response_inside_the_window(synchronous_native_client):
    """`on_reconnect` must not arm the announcement it is about to suppress.

    It reports PNReconnectedCategory and sets the latch itself. If the restart
    cleared the latch first, a subscribe response arriving before that
    assignment would announce PNConnectedCategory as well.
    """
    pubnub, recorder, stub = synchronous_native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    recorder.categories.clear()

    stub.answer_synchronously = True
    pubnub._subscription_manager._reconnection_listener.on_reconnect()

    assert recorder.categories == [PNStatusCategory.PNReconnectedCategory]


def test_native_partial_unsubscribe_announces_nothing(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL, OTHER_CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    recorder.categories.clear()

    pubnub._subscription_manager.adapt_unsubscribe_builder(
        UnsubscribeOperation(channels=[OTHER_CHANNEL], channel_groups=[])
    )
    deliver_native_response(stub, timetoken=1001)

    assert recorder.categories == []


def test_native_unsubscribe_all_then_subscribe_announces_connected(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    pubnub.unsubscribe_all()
    recorder.categories.clear()

    pubnub.subscribe().channels([OTHER_CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1001)

    assert recorder.categories == [PNStatusCategory.PNConnectedCategory]


def test_native_set_state_announces_nothing(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    recorder.categories.clear()

    pubnub.set_state().channels([CHANNEL]).state({"mood": "ok"}).custom_params()
    deliver_native_response(stub, timetoken=1001)

    assert recorder.categories == []


def test_native_reconnect_restarts_the_subscribe_loop(native_client):
    pubnub, recorder, stub = native_client

    pubnub.subscribe().channels([CHANNEL]).execute()
    deliver_native_response(stub, timetoken=1000)
    before = stub.request_count

    pubnub.reconnect()

    assert stub.request_count > before
