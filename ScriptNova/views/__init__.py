"""
Views module for ScriptNova app.

Import all views here for cleaner organization.
"""

from .Authentication import signupAPI, loginAPI, getByIdApi, updateAPI

__all__ = ['signupAPI', 'loginAPI', 'getByIdApi', 'updateAPI']
