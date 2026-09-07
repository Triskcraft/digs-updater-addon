from unittest import TestCase
from unittest.mock import patch

import __init__ as addon_module


class MdaddonUnloadTests(TestCase):
    def test_unload_when_configuration_is_missing(self) -> None:
        with patch.object(addon_module, "getenv", return_value=None):
            addon = addon_module.mdaddon(None)  # type: ignore[arg-type]

        self.assertIsNone(addon._chron_task)
        addon.unload()
