from abc import ABCMeta, abstractmethod


class BaseRequestHandler:
    __metaclass__ = ABCMeta

    @abstractmethod
    def sync_request(self, platform_options, endpoint_call_options):
        pass

    @abstractmethod
    def async_request(
        self,
        endpoint_name,
        platform_options,
        endpoint_call_options,
        callback,
        cancellation_event,
    ):
        pass
