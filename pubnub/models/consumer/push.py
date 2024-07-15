class PNPushAddChannelResult:
    def __str__(self):
        return "Channel successfully added"


class PNPushRemoveChannelResult:
    def __str__(self):
        return "Channel successfully removed"


class PNPushRemoveAllChannelsResult:
    def __str__(self):
        return "All channels successfully removed"


class PNPushListProvisionsResult:
    def __init__(self, channels):
        self.channels = channels

    def __str__(self):
        return "Push notification enabled on following channels: %s" % ", ".join(
            self.channels
        )
