#!/usr/bin/env python3
import tempfile
from pathlib import Path

import qloader


def test_google_images_query_chrome_100() -> None:
    output_path = Path(tempfile.TemporaryDirectory().name)
    metadata_path = Path(__file__).parent.joinpath("test-metadata.json")
    max_items = 100

    images_metadata = qloader.run(
        endpoint="google-images",
        query_terms="cute dog",
        output_path=output_path,
        metadata=metadata_path,
        max_items=max_items,
        language="en",
        browser="Chrome",
        keep_head=False,
    )

    assert (len(images_metadata) / max_items) > 0.95  # assert 95% fill rate

    for image_metadata in images_metadata:
        assert (
            image_metadata["test-key"] == "test-value"
        )  # assert metadata is propagated

    assert (
        len([p for p in output_path.iterdir()]) / max_items
    ) > 0.95  # assert images are on disk


def test_google_images_query_firefox_10() -> None:
    output_path = Path(tempfile.TemporaryDirectory().name)
    metadata_path = Path(__file__).parent.joinpath("test-metadata.json")
    max_items = 10

    images_metadata = qloader.run(
        endpoint="google-images",
        query_terms="cutest dog",
        output_path=output_path,
        metadata=metadata_path,
        max_items=max_items,
        language="en",
        browser="Firefox",
        keep_head=False,
    )

    assert (len(images_metadata) / max_items) > 0.95  # assert 95% fill rate

    for image_metadata in images_metadata:
        assert (
            image_metadata["test-key"] == "test-value"
        )  # assert metadata is propagated

    assert (
        len([p for p in output_path.iterdir()]) / max_items
    ) > 0.95  # assert images are on disk


def test_google_images_region_specific_query_20() -> None:
    output_path = Path(tempfile.TemporaryDirectory().name)
    metadata_path = Path(__file__).parent.joinpath("test-metadata.json")
    max_items = 20

    images_metadata = qloader.run(
        endpoint="google-images",
        query_terms="vieux chien",
        output_path=output_path,
        metadata=metadata_path,
        max_items=max_items,
        language="fr",
        browser="Chrome",
        extra_query_params={"cr": "countryFR"},
        keep_head=False,
    )

    assert (
        len([p for p in output_path.iterdir()]) / max_items
    ) > 0.95  # assert images are on disk


def test_google_images_track_related_10() -> None:
    output_path = Path(tempfile.TemporaryDirectory().name)
    metadata_path = Path(__file__).parent.joinpath("test-metadata.json")
    max_items = 10

    images_metadata = qloader.run(
        endpoint="google-images",
        query_terms="poodle",
        output_path=output_path,
        metadata=metadata_path,
        max_items=max_items,
        language="en",
        browser="Chrome",
        extra_query_params={"cr": "countryCA"},
        track_related=True,
        keep_head=False,
    )


# def test_google_images_query_chrome_10_proxied() -> None:
#    output_path = Path(tempfile.TemporaryDirectory().name)
#    metadata_path = Path(__file__).parent.joinpath("test-metadata.json")
#    max_items = 10
#
#    images_metadata = qloader.run(
#        endpoint="google-images",
#        query_terms="my location",
#        output_path=output_path,
#        metadata=metadata_path,
#        max_items=max_items,
#        language="en",
#        browser="Chrome",
#        keep_head=False,
#        use_proxy="http://localhost:8181"
#    )
#
#    assert (len(images_metadata) / max_items) > 0.80  # assert 80% fill rate
#
#    for image_metadata in images_metadata:
#        assert (
#            image_metadata["test-key"] == "test-value"
#        )  # assert metadata is propagated
#
#    assert (
#        len([p for p in output_path.iterdir()]) / max_items
#    ) > 0.80  # assert images are on disk
