#!/usr/bin/env python3
from __future__ import annotations
import argparse
import base64
import io
import os
import json
import time
import traceback
from collections import defaultdict, UserDict
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlparse

import boto3
import requests
from PIL import Image, UnidentifiedImageError

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions

from browserdriver import fetch_google_image_urls

"""

This program gathers search engine results by running a query against some endpoint. 
Metadata about the queries (host IP geolocation information, query context) are used to tag results.

The first search engine implemented here is google_images. Image files are downloaded by a selenium webdriver.

Additional endpoints can be implemented by writing a corresponding get_<endpoint> method in this module.

By default, this program attempts to store results in some S3 interface, but this requires configuration of secret values. Results are stored locally as well, and the S3 upload can be skipped by passing --skip-upload.
"""

BROWSER = os.getenv("QLOADER_BROWSER", "Firefox")
browser_options = {"Firefox": FirefoxOptions(), "Chrome": ChromeOptions()}

# Configure browser options through this object (user agent, headless, etc)
OPTIONS = browser_options[BROWSER]
OPTIONS.add_argument("--headless")
if BROWSER == "Chrome":
    OPTIONS.add_argument("--no-sandbox")

# Only necessary if --skip-upload is not set
ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "https://fra1.digitaloceanspaces.com")
S3_ENDPOINT_URL = None if S3_ENDPOINT_URL in ["", "None"] else S3_ENDPOINT_URL
S3_REGION_NAME = os.getenv("S3_REGION_NAME", "fra1")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "qload")


def get_s3_client() -> botocore.client.s3:
    """
        Results can be stored in S3
    """
    assert ACCESS_KEY_ID is not None
    assert SECRET_ACCESS_KEY is not None
    session = boto3.session.Session()
    return session.client(
        "s3",
        region_name=S3_REGION_NAME,
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_ACCESS_KEY,
    )


def persist_image(folder: Path, image_id: str, url: str) -> None:
    """
        Write image to disk
    """
    folder.mkdir(exist_ok=True, parents=True)
    image_content = requests.get(url, timeout=30).content
    image = Image.open(io.BytesIO(image_content)).convert("RGB")
    image_file = folder.joinpath(image_id + ".jpg")
    with open(image_file, "w") as f:
        image.resize((300, 300), Image.ANTIALIAS).save(
            f, "JPEG", optimize=True, quality=85
        )


class ManifestDocument(UserDict):
    """
        This placeholder class is where we could formalize a data structure for the output
    """

    pass


def get_google_images(
    query_terms: str, store: Path, max_images: int
) -> Generator[ManifestDocument, None, None]:
    """
        Save images to disk and yield a ManifestDocument for each image
    """
    store.mkdir(parents=True, exist_ok=True)
    errors = defaultdict(int)
    with getattr(webdriver, BROWSER)(options=OPTIONS, log_path=Path(__file__).parent.joinpath("/tmp/driver.log")) as driver:
        wait = WebDriverWait(driver, 10)
        i = 0
        for image_url in fetch_google_image_urls(
            query=query_terms,
            driver=driver,
            sleep_between_interactions=0.3,
            desired_count=max_images,
        ):
            image_id = uuid4().hex
            try:
                persist_image(store, image_id, image_url)
                i += 1
                print(f"{i}: saved {image_url}")
                yield ManifestDocument(
                    {
                        "query": query_terms,
                        "image_id": image_id,
                        "image_url": image_url,
                    }
                )
            except Exception as e:
                traceback.print_exc()
                errors[str(type(e))] += 1
    total_errors = sum(errors.values())
    print(f"retrieved {i} images from google images with {total_errors} errors")
    if total_errors > 0:
        print(json.dumps(errors, indent=2))


class UnimplementedEndpointError(Exception):
    pass


class NoDocumentsReturnedError(Exception):
    pass


def main(
    trial_id: str,
    ran_at: str,
    hostname: str,
    endpoint: str,
    query_terms: str,
    output_path: Path,
    metadata_path: Path,
    max_images: int,
    upload_to_s3: bool = True,
) -> None:
    output_path = (
        output_path.joinpath(trial_id).joinpath(hostname).joinpath(ran_at)
    )  # make each run it's own folder
    output_path.mkdir(parents=True, exist_ok=True)
    endpoint = endpoint.replace(
        "-", "_"
    )  # We will be using this string to find an appropriate getter method in this module
    manifest = output_path.joinpath("manifest.json")
    store = output_path.joinpath("images")
    if metadata_path.is_file():
        metadata = json.loads(metadata_path.read_text())
    else:
        print(
            f"WARNING: no metadata file found {metadata_path}. No host-level metadata will be included with results"
        )
        metadata = dict()
    metadata.update({"endpoint": endpoint})
    metadata.update({"ran_at": ran_at})
    documents = []
    try:
        for doc in globals()[f"get_{endpoint}"](query_terms, store, max_images):
            doc.update(metadata)
            documents.append(doc)
    except KeyError as e:
        raise UnimplementedEndpointError(
            f"No get_{endpoint} method could be found in {__file__}"
        )

    if len(documents) == 0:
        raise NoDocumentsReturnedError(f"get_{endpoint} yielded no documents")

    manifest.write_text(json.dumps([dict(d) for d in documents], indent=2,))
    if upload_to_s3:
        s3_client = get_s3_client()

        remote_path_root = Path(
            f"data/{trial_id}/{hostname}/{query_terms.replace(' ', '_')}/{ran_at}"
        )
        remote_manifest_path = remote_path_root.joinpath("manifest.json")
        print("uploading file:", str(manifest), BUCKET_NAME, str(remote_manifest_path))
        s3_client.upload_file(str(manifest), BUCKET_NAME, str(remote_manifest_path))

        for image_path in store.iterdir():
            s3_client.upload_file(
                str(image_path),
                BUCKET_NAME,
                str(remote_path_root.joinpath(f"images/{image_path.name}")),
            )

    print(
        f'{trial_id} - "{query_terms}" completed query against {endpoint}, images gathered here: {store}.'
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial-id", required=True)
    parser.add_argument(
        "--ran-at", required=True, help="timestamp of when this query was run"
    )
    parser.add_argument(
        "--hostname", required=True, help="The name of the computer running the query"
    )
    parser.add_argument(
        "--endpoint",
        required=False,
        default="google-images",
        help="The endpoint to query, only google-images is currently implemented",
    )
    parser.add_argument(
        "--metadata-path",
        required=True,
        help="JSON file with metadata to associate with query results",
    )
    parser.add_argument(
        "--output-path", required=True, help="Where to store results locally",
    )
    parser.add_argument("--query-terms", required=True)
    parser.add_argument("--max-images", type=int, default=100)
    parser.add_argument(
        "--skip-upload",
        action="store_true",
        help="Skip S3 upload step for local-only analysis",
    )
    args = parser.parse_args()
    main(
        trial_id=args.trial_id,
        ran_at=args.ran_at,
        hostname=args.hostname,
        endpoint=args.endpoint,
        query_terms=args.query_terms,
        output_path=Path(args.output_path),
        metadata_path=Path(args.metadata_path),
        max_images=args.max_images,
        upload_to_s3=not args.skip_upload,
    )
