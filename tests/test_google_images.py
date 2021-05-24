#!/usr/bin/env python3
import tempfile
from pathlib import Path

from qloader.query import query

def test_google_images_query() -> None:
    output_path = Path(tempfile.TemporaryDirectory().name)
    metadata_path = Path(__file__).parent.joinpath("test-metadata.json")
    max_items = 100

    images_metadata = query(
        endpoint="google-images",
        query_terms="cute dog",
        output_path=output_path,
        metadata_path=metadata_path,
        max_items=max_items,
        language="en",
        browser="Firefox"
    )

    assert (len(images_metadata) / max_items) > 0.95 # assert 95% fill rate

    for image_metadata in images_metadata:
        assert image_metadata["test-key"] == "test-value" # assert metadata is propagated

    assert (len([p for p in output_path.iterdir()]) / max_items) > 0.95 # assert images are on disk