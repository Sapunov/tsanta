class ConfirmationError(Exception):

    def __init__(self, message='Неверный адрес для подтверждения', errors=None):

        super(ConfirmationError, self).__init__(message)
        self.errors = errors
