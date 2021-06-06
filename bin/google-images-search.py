#!/usr/bin/env python3
import argparse
import tempfile
from pathlib import Path

import qloader


def main(args: argparse.Namespace) -> None:
    images_metadata = qloader.run(
        endpoint="google-images",
        query_terms=args.query,
        output_path=args.output_path,
        metadata=None,
        max_items=args.max_items,
        language=args.language,
        browser=args.browser,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--query", required=True, type=str, help="what to search")
    parser.add_argument("--language", type=str, help="language of query", default="en")
    parser.add_argument(
        "--output-path",
        type=Path,
        help="path to save output",
        default=Path(tempfile.TemporaryDirectory().name),
    )
    parser.add_argument(
        "--max-items", type=int, help="number of images to aim for", default=100
    )
    parser.add_argument(
        "--browser", type=str, help="Browser to use for searching", default="Firefox"
    )

    main(parser.parse_args())
