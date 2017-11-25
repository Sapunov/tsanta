from rest_framework.exceptions import ValidationError


class TSantaException(Exception):

    pass


class AlreadySignedException(TSantaException):

    pass
