# readstore-basic/frontend/streamlit/exceptions.py

"""
Module containing custom exceptions for streamlit UI.

Classes:
    - UIAppError: Base class for UI exceptions.

"""

class UIAppError(Exception):
    """Base class for UI exceptions."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
