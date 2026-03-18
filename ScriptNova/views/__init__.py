"""
Views module for ScriptNova app.

Import all views here for cleaner organization.
"""

from os import __all__

from .Authentication import signupAPI, loginAPI, getByIdApi, updateAPI
from .Blogs import GenerateBlog, GenerateKeywords

__all__ = [
  'signupAPI',
  'loginAPI',
  'getByIdApi',
  'updateAPI',
  'GenerateBlog',
  'GenerateKeywords',
  ]
