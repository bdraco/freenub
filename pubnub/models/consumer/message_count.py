class PNMessageCountResult:
    def __init__(self, result):
        """
        Representation of message count server response

        :param result: result of message count operation
        """
        self._result = result
        self.channels = result["channels"]

    def __str__(self):
        return f"Message count for channels: {self.channels}"
