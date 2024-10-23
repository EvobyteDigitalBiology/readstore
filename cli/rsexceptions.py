# readstore-basic/cli/rsexceptions.py

class ReadStoreError(Exception):
    """Base class for ReadStoreError exceptions."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
