class PywrParserException(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

    def __repr__(self):
        return f"{self.__class__.__qualname__}({self.message})"


class PywrTypeValidationError(PywrParserException):
    def __init__(self, message, source=None, component=None):
        super().__init__(message)
        self.source = source if source else {}
        self.component = component if component else ""

    def __str__(self):
        return super().__str__() + '\n' + "\n".join(self.rules_failed)


class PywrNetworkValidationError(PywrParserException):
    def __init__(self, message):
        super().__init__(message)
