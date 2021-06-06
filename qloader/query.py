"""
This program gathers search engine results by running a query against some endpoint.
Metadata about the queries (host IP geolocation information, query context) are used to tag results.

The first search engine implemented here is google_images. Image files are downloaded by a selenium webdriver.
Additional endpoints can be implemented by writing a corresponding get_<endpoint> method in this module.
"""
from __future__ import annotations

import argparse
import io
import os
import hashlib
import json
import traceback
import logging
from collections import defaultdict, UserDict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import imagehash
import requests
from PIL import Image, UnidentifiedImageError
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

from .args import get_parser
from .browserdriver import fetch_google_image_urls, get_browser_options
from .logger import get_logger


def hash_image(image: Image, image_url: str) -> str:
    """
    """
    hash_tuple = (imagehash.colorhash(image), imagehash.average_hash(image))
    name = ""
    for hash_component in hash_tuple:
        for char in hash_component.hash.flatten():
            if char:
                name += "0"
            else:
                name += "I"

    return hashlib.md5((image_url + name).encode("utf-8")).hexdigest()


def persist_image(folder: Path, url: str) -> None:
    """
        Write image to disk
    """
    folder.mkdir(exist_ok=True, parents=True)
    image_content = requests.get(url, timeout=30).content
    image = Image.open(io.BytesIO(image_content)).convert("RGB")
    image_id = hash_image(image, url)
    image_file = folder.joinpath(image_id + ".jpg")
    with open(image_file, "w") as f:
        image.save(f, "JPEG", optimize=True, quality=85)
    return image_id


class ManifestDocument(UserDict):
    """
        This placeholder class is where we could formalize a data structure for the output
    """

    pass


def get_url_headers(image_url: str) -> Dict[str, Any]:

    url_headers = requests.head(image_url).headers

    headers = {
        header_key.replace("-", "_"): url_headers[header_key]
        for header_key in ["last-modified", "content-type", "content-length", "server"]
        if header_key in url_headers
    }

    if "last_modified" in headers:
        # turn last_modified date into ms since epoch
        headers["last_modified"] = int(
            datetime.strptime(
                headers["last_modified"], "%a, %d %b %Y %H:%M:%S %Z"
            ).timestamp()
            * 1000
        )

    return headers


class UnacceptableErrorRateError(Exception):
    pass


def get_google_images(
    query_terms: str,
    store: Path,
    max_items: int,
    language: str,
    browser: str,
    acceptable_error_rate: float,
    extra_query_params: Optional[Dict[str, str]] = None,
) -> Generator[ManifestDocument, None, None]:
    """
        Save images to disk and yield a ManifestDocument for each image
    """
    log = get_logger("get_google_images")

    store.mkdir(parents=True, exist_ok=True)
    errors = defaultdict(int)
    browser_options = get_browser_options(browser)
    with getattr(webdriver, browser)(
        options=browser_options,
        service_log_path=Path(__file__).parent.joinpath("driver.log"),
    ) as driver:
        wait = WebDriverWait(driver, 10)
        i = 0
        for image_url in fetch_google_image_urls(
            query=query_terms,
            driver=driver,
            sleep_between_interactions=0.3,
            desired_count=max_items,
            language=language,
            extra_query_params=extra_query_params,
        ):
            try:
                image_id = persist_image(store, image_url)
                i += 1
                log.debug(f"{i}: saved {image_url}")
                yield ManifestDocument(
                    {
                        "query": query_terms,
                        "image_id": image_id,
                        "image_url": image_url,
                        "headers": get_url_headers(image_url),
                    }
                )
            except Exception as e:
                # show errors during image gathering for debugging, but accept that some urls will not work.
                # traceback.print_exc()
                errors[str(type(e))] += 1

    total_errors = sum(errors.values())
    log.debug(f"retrieved {i} images from google images with {total_errors} errors")
    if total_errors > 0:
        log.debug(json.dumps(errors, indent=2))

    if (len(errors) / max_items) > acceptable_error_rate:
        raise UnacceptableErrorRateError(
            f"{len(errors)}/{max_items} images failed to download!"
        )


class UnimplementedEndpointError(Exception):
    pass


class NoDocumentsReturnedError(Exception):
    pass


def run(
    endpoint: str,
    query_terms: str,
    output_path: Path,
    max_items: int,
    metadata: Optional[Union[Path, str, Dict[str, Any]]] = None,
    language: str = "en",
    browser: str = "Firefox",
    manifest_file: Optional[Union[str, Path]] = None,
    acceptable_error_rate: float = 0.06,
    extra_query_params: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Executes a query and returns a list of objects returned by that query, may also leave data on disk at {output_path} 
    depending on the endpoint and type of data.
    """
    output_path.mkdir(parents=True, exist_ok=True)

    log = get_logger("run")

    if metadata is not None:
        if isinstance(metadata, Path) or isinstance(metadata, str):
            metadata = json.loads(Path(metadata).read_text())
        elif isinstance(metadata, dict):
            metadata = metadata
    else:
        metadata = dict()

    metadata.update({"endpoint": endpoint})

    documents = []
    if endpoint == "google-images":
        for doc in get_google_images(
            query_terms,
            output_path,
            max_items,
            language,
            browser,
            acceptable_error_rate,
            extra_query_params,
        ):
            doc.update(metadata)
            documents.append(doc)
    else:
        raise UnimplementedEndpointError(
            f"No get_{endpoint} method could be found in {__file__}"
        )

    if len(documents) == 0:
        raise NoDocumentsReturnedError(f"{endpoint} yielded no documents")

    if manifest_file is not None:
        Path(manifest_file).write_text(
            json.dumps([dict(d) for d in documents], indent=2,)
        )

    log.info(
        f'"{query_terms}" completed query against {endpoint}, images gathered here: {output_path}.'
    )
    return documents
