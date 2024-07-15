class PNMessageAction:
    def __init__(self, message_action=None):
        if message_action is not None:
            self.type = message_action["type"]
            self.value = message_action["value"]
            self.message_timetoken = message_action["messageTimetoken"]
            self.uuid = message_action["uuid"]
            self.action_timetoken = message_action["actionTimetoken"]
        else:
            self.type = None
            self.value = None
            self.message_timetoken = None
            self.uuid = None
            self.action_timetoken = None

    def __str__(self):
        return f"Message action with tt: {self.action_timetoken} for uuid {self.uuid} with value {self.value} "


class PNGetMessageActionsResult:
    def __init__(self, result):
        """
        Representation of get message actions server response

        :param result: result of get message actions operation
        """
        self._result = result
        self.actions = result["actions"]

    def __str__(self):
        return "Get message actions success"


class PNAddMessageActionResult(PNMessageAction):
    def __init__(self, message_action):
        super().__init__(message_action)


class PNRemoveMessageActionResult:
    def __init__(self, result):
        """
        s
        Representation of remove message actions server response

        :param result: result of remove message actions operation
        """
        self._result = result

    def __str__(self):
        return "Remove message actions success"
