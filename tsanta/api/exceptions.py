from rest_framework.exceptions import ValidationError


class TSantaException(Exception):

    pass


class AlreadySignedException(TSantaException):

    pass


class KeyExistsException(TSantaException):

    pass

class UnsupportedKeyType(TSantaException):

    pass


class AssignWardError(TSantaException):

    pass
