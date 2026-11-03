"""Looks up real medical devices in the FDA's free public database (openFDA).

Used when a nurse describes something that isn't in our catalog: we can show
real products that match, whether they're still sold, and any recalls.
No key needed. Docs: https://open.fda.gov/apis/device/
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

FDA_URL = "https://api.fda.gov/device"
TIMEOUT_SECONDS = 5  # a slow FDA site must never leave a nurse waiting long
MAX_WORDS = 6


class FdaError(Exception):
    """The FDA site couldn't be reached or sent something unexpected."""


class FdaRecall(BaseModel):
    date: str | None
    status: str | None  # e.g. "Ongoing" or "Terminated"
    reason: str | None


class FdaDevice(BaseModel):
    brand: str | None
    company: str
    model_number: str | None  # what hospitals usually call the MPN or catalog number
    description: str
    in_distribution: bool  # still being sold, per the FDA listing
    recalls: list[FdaRecall] = []
    recalls_checked: bool = False  # False if the recall lookup failed, so "no recalls" isn't claimed


def _get(path: str, search: str, limit: int) -> list[dict]:
    """One openFDA request. No matches comes back as an empty list."""
    query = urllib.parse.urlencode({"search": search, "limit": limit})
    try:
        with urllib.request.urlopen(f"{FDA_URL}/{path}.json?{query}", timeout=TIMEOUT_SECONDS) as response:
            return json.load(response).get("results", [])
    except urllib.error.HTTPError as error:
        if error.code == 404:  # openFDA's way of saying "nothing found"
            return []
        raise FdaError(f"FDA lookup failed ({error.code})") from error
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        raise FdaError("FDA lookup unavailable") from error


def _words(text: str) -> list[str]:
    """'Lap sponge, x-ray 18x18' -> ['Lap', 'sponge', 'x', 'ray', '18x18']"""
    return re.findall(r"[A-Za-z0-9]+", text)[:MAX_WORDS]


def _quote(text: str) -> str:
    return '"' + text.replace('"', "") + '"'


def _to_device(record: dict) -> FdaDevice:
    return FdaDevice(
        brand=record.get("brand_name"),
        company=record.get("company_name") or "Unknown maker",
        model_number=record.get("catalog_number") or record.get("version_or_model_number"),
        description=record.get("device_description") or record.get("brand_name") or "",
        in_distribution=record.get("commercial_distribution_status") == "In Commercial Distribution",
    )


def find_recalls(device: FdaDevice) -> list[FdaRecall]:
    """Recalls by the same company that name this model number."""
    if not device.model_number:
        return []
    firm = _words(device.company)[:1]  # "DeRoyal Industries Inc" -> "DeRoyal"
    if not firm:
        return []
    search = f"recalling_firm:{_quote(firm[0])} AND product_description:{_quote(device.model_number)}"
    return [
        FdaRecall(
            date=r.get("event_date_initiated"),
            status=r.get("recall_status"),
            reason=r.get("reason_for_recall"),
        )
        for r in _get("recall", search, limit=3)
    ]


def search_devices(description: str, limit: int = 5) -> list[FdaDevice]:
    """Real devices whose FDA description contains every word, still-sold ones first."""
    words = _words(description)
    if not words:
        return []
    records = _get("udi", f"device_description:({' AND '.join(words)})", limit=25)

    # The FDA lists each box size separately, so keep one per company + model
    devices, seen = [], set()
    for record in records:
        device = _to_device(record)
        key = (device.company.lower(), (device.model_number or device.description).lower())
        if key not in seen:
            seen.add(key)
            devices.append(device)
    devices.sort(key=lambda d: not d.in_distribution)  # still sold first
    devices = devices[:limit]

    # Check recalls for all of them at the same time, not one after another
    with ThreadPoolExecutor(max_workers=max(len(devices), 1)) as pool:
        for device, recalls in zip(devices, pool.map(_recalls_or_none, devices)):
            if recalls is not None:
                device.recalls = recalls
                device.recalls_checked = True
    return devices


def _recalls_or_none(device: FdaDevice) -> list[FdaRecall] | None:
    """A failed recall check shouldn't hide the devices we already found."""
    try:
        return find_recalls(device)
    except FdaError:
        return None
