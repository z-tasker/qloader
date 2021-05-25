from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path


class EnvDefault(argparse.Action):
    """
        An argparse action class that auto-sets missing default values from env vars. 
        Defaults to requiring the argument, meaning an error will be thrown if no value 
        was directly passed to argparse and the env_default returned None as well.
    """

    def __init__(self, envvar, required=True, default=None, **kwargs):
        if envvar in os.environ:
            default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)


def env_default(envvar):
    """ functional sugar for EnvDefault """

    def wrapper(**kwargs):
        return EnvDefault(envvar, **kwargs)

    return wrapper


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--endpoint",
        type=str,
        action=env_default("QLOADER_ENDPOINT"),
        default="google-images",
        help="The endpoint to query, only google-images is currently implemented",
    )
    parser.add_argument(
        "--metadata-path",
        type=Path,
        action=env_default("QLOADER_METADATA_PATH"),
        required=False,
        help="JSON file with metadata to associate with query results",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        action=env_default("QLOADER_OUTPUT_PATH"),
        default=Path(tempfile.TemporaryDirectory().name),
        help="Where to store results locally",
    )
    parser.add_argument(
        "--query-terms",
        type=str,
        action=env_default("QLOADER_QUERY_TERMS"),
        required=True,
        help="Input into whatever endpoint is being searched",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        action=env_default("QLOADER_MAX_ITEMS"),
        default=100,
        help="Max number of items to retrieve from endpoint",
    )
    parser.add_argument(
        "--language",
        type=str,
        action=env_default("QLOADER_LANGUAGE"),
        default="en",
        help="Add some language specificity to the query",
    )
    parser.add_argument(
        "--browser",
        type=str,
        action=env_default("QLOADER_BROWSER"),
        default="Firefox",
        help="Browser to use for webdriver, if needed",
    )

    return parser
