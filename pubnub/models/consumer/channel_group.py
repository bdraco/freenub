class PNChannelGroupsAddChannelResult:
    def __str__(self):
        return "Channel successfully added"


class PNChannelGroupsRemoveChannelResult:
    def __str__(self):
        return "Channel successfully removed"


class PNChannelGroupsRemoveGroupResult:
    def __str__(self):
        return "Group successfully removed"


class PNChannelGroupsListResult:
    def __init__(self, channels):
        self.channels = channels

    def __str__(self):
        return "Group contains following channels: %s" % ", ".join(self.channels)
