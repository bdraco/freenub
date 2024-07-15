from pubnub.models.consumer.objects_v2.page import PNPageable


class PNSetChannelMetadataResult:
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Set Channel metatdata: %s" % self.data


class PNGetChannelMetadataResult:
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get Channel metatdata: %s" % self.data


class PNRemoveChannelMetadataResult:
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get Channel metatdata: %s" % self.data


class PNGetAllChannelMetadataResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get all Channel metatdata: %s" % self.data


class PNChannelMetadataResult:
    def __init__(self, event, data):
        self.data = data
        self.event = event

    def __str__(self):
        return f"Channel {self.event} event with data: {self.data}"
