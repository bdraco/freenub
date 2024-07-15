from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, UuidEndpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.objects_v2.uuid import PNRemoveUUIDMetadataResult


class RemoveUuid(ObjectsEndpoint, UuidEndpoint):
    REMOVE_UID_PATH = "/v2/objects/%s/uuids/%s"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self)

    def build_path(self):
        return RemoveUuid.REMOVE_UID_PATH % (
            self.pubnub.config.subscribe_key,
            self._effective_uuid(),
        )

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope):
        return PNRemoveUUIDMetadataResult(envelope)

    def operation_type(self):
        return PNOperationType.PNRemoveUuidMetadataOperation

    def name(self):
        return "Remove UUID"

    def http_method(self):
        return HttpMethod.DELETE
