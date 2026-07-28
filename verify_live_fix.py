#!/usr/bin/env python3
"""Read-only verification of the eight corrected JPL CAD records."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from decimal import Decimal


OBJECTS = (
    "367943",
    "2019 DP",
    "2019 XN3",
    "2021 VH2",
    "2022 NJ",
    "2018 QE",
    "2016 SW3",
    "2020 OO1",
)
EXPECTED_EVENT_DATES = {
    "367943": "2004-Aug-19",
    "2019 DP": "2019-Feb-23",
    "2019 XN3": "2019-Dec-14",
    "2021 VH2": "2021-Nov-11",
    "2022 NJ": "2022-Jul-15",
    "2018 QE": "2024-Oct-12",
    "2016 SW3": "2016-Sep-26",
    "2020 OO1": "2020-Jul-27",
}
API = "https://ssd-api.jpl.nasa.gov/cad.api"


def fetch(designation: str) -> dict:
    query = urllib.parse.urlencode(
        {
            "des": designation,
            "date-min": "1900-01-01",
            "date-max": "2100-01-01",
            "dist-max": "0.2",
            "body": "Earth",
        }
    )
    request = urllib.request.Request(
        f"{API}?{query}",
        headers={"User-Agent": "Project-Aletheia-public-verifier/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def violations(payload: dict) -> list[dict[str, str]]:
    fields = {name: index for index, name in enumerate(payload["fields"])}
    result = []
    for row in payload.get("data", []):
        values = [row[fields[name]] for name in ("dist", "dist_min", "dist_max")]
        if any(value is None for value in values):
            continue
        distance, minimum, maximum = map(Decimal, values)
        if not minimum <= distance <= maximum:
            result.append(
                {
                    "date": row[fields["cd"]],
                    "dist": str(distance),
                    "dist_min": str(minimum),
                    "dist_max": str(maximum),
                }
            )
    return result


def main() -> int:
    rows = []
    for designation in OBJECTS:
        payload = fetch(designation)
        bad = violations(payload)
        fields = {name: index for index, name in enumerate(payload["fields"])}
        expected_rows = [
            row
            for row in payload.get("data", [])
            if str(row[fields["cd"]]).startswith(EXPECTED_EVENT_DATES[designation])
        ]
        expected_event_found = bool(expected_rows)
        expected_event_valid = bool(expected_rows) and all(
            all(row[fields[name]] is not None for name in ("dist", "dist_min", "dist_max"))
            and Decimal(row[fields["dist_min"]])
            <= Decimal(row[fields["dist"]])
            <= Decimal(row[fields["dist_max"]])
            for row in expected_rows
        )
        rows.append(
            {
                "designation": designation,
                "rows_checked": len(payload.get("data", [])),
                "expected_event_found": expected_event_found,
                "expected_event_valid": expected_event_valid,
                "violations": bad,
            }
        )
        print(
            f"{designation}: {len(payload.get('data', []))} rows, "
            f"expected event {'valid' if expected_event_valid else 'MISSING/INVALID'}, "
            f"{len(bad)} violations"
        )

    passed = sum(
        row["rows_checked"] >= 1
        and row["expected_event_valid"]
        and not row["violations"]
        for row in rows
    )
    if passed == len(OBJECTS):
        print(f"PASS: {passed} of {len(OBJECTS)} reported objects have zero distance-order violations")
        return 0
    print(
        f"FAIL: {len(OBJECTS) - passed} reported objects have a missing/invalid "
        "expected event or another distance-order violation"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
