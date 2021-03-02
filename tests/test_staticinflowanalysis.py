# Core Library
import ast
from typing import Set

# First party
from staticinflowanalysis import Plugin

"""Tests for `staticinflowanalysis` package."""

# Third party modules
import pytest

# First party modules
import staticinflowanalysis


def _results(s: str) -> Set[str]:
    tree = ast.parse(s)
    plugin = Plugin(tree)
    return {f"{line}:{col} {msg}" for line, col, msg, _ in plugin.run()}


def test_trivial_case():
    assert _results("") == set()


def test_plugin_version():
    assert isinstance(Plugin.version, str)
    assert "." in Plugin.version

def test_plugin_name():
    assert isinstance(Plugin.name, str)

