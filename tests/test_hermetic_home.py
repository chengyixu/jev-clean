"""Hermetic tests never touch the real account's HOME.

In-process CLI tests once used the real ~/.local/state/jev-clean: they wrote state there
and failed with "Another jev-clean run is active" whenever the user had jev-clean open.
"""

import os
import pwd
from pathlib import Path


def test_tests_run_with_a_temporary_home_not_the_account_home():
    account_home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    assert Path.home() != account_home
    assert not Path.home().is_relative_to(account_home)
