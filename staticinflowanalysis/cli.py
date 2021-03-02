#!/usr/bin/env python

# Third party modules
import click

# First party modules
import staticinflowanalysis


@click.group()
@click.version_option(version=staticinflowanalysis.__version__)
def entry_point():
    """Awesomeproject spreads pure awesomeness."""
