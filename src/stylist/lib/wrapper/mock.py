from __future__ import absolute_import

import sys
from pytest_mock import MockFixture


def _get_mock_module():
    """
    Import and return the actual "mock" module. By default this is "mock" for Python 2 and
    "unittest.mock" for Python 3, but the user can force to always use "mock" on Python 3 using
    the mock_use_standalone_module ini option.
    """
    if not hasattr(_get_mock_module, '_module'):
        use_standalone_module = False
        if sys.version_info[0] == 2 or use_standalone_module:
            import mock
            _get_mock_module._module = mock
        else:
            import unittest.mock
            _get_mock_module._module = unittest.mock

    return _get_mock_module._module


class Mocker(MockFixture):
    def __init__(self):
        self._patches = []  # list of mock._patch objects
        self._mocks = []  # list of MagicMock objects
        self.mock_module = mock_module = _get_mock_module()
        self.patch = self._Patcher(self._patches, self._mocks, mock_module)
        # aliases for convenience
        self.Mock = mock_module.Mock
        self.MagicMock = mock_module.MagicMock
        self.PropertyMock = mock_module.PropertyMock
        self.call = mock_module.call
        self.ANY = mock_module.ANY
        self.DEFAULT = mock_module.DEFAULT
        self.sentinel = mock_module.sentinel
        self.mock_open = mock_module.mock_open
