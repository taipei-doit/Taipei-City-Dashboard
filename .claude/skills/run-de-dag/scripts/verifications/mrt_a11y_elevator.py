"""
DAG-specific verification for mrt_a11y_elevator.

Tests business logic that the generic verifier cannot know:
- row count ≈ 188 (sample-validated 2026-04-25)
- facility_type ⊆ {elevator, ramp, other} and 'other' < 10%
- station unique count between 110 and 125
"""
import re

_TABLE_NAME_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$')


def _safe_table(name):
    if not _TABLE_NAME_RE.match(name):
        raise ValueError(f"Invalid table name: {name!r}")
    return name

EXPECTED_ROWS = 188
ROW_TOLERANCE = 0.05
ALLOWED_FACILITY_TYPES = {"elevator", "ramp", "other"}
OTHER_THRESHOLD = 0.10
EXPECTED_UNIQUE_STATIONS = (110, 125)


def verify(hook, config):
    results = []
    table = _safe_table(config["ready_data_default_table"])

    row_count = hook.get_first(f"SELECT COUNT(*) FROM {table}")[0]
    lo = int(EXPECTED_ROWS * (1 - ROW_TOLERANCE))
    hi = int(EXPECTED_ROWS * (1 + ROW_TOLERANCE))
    results.append(
        (
            f"row count ≈ {EXPECTED_ROWS} (±{int(ROW_TOLERANCE*100)}%)",
            lo <= row_count <= hi,
            f"actual={row_count}, expected={lo}–{hi}",
        )
    )

    types = {
        r[0] for r in hook.get_records(f"SELECT DISTINCT facility_type FROM {table}")
    }
    unknown = types - ALLOWED_FACILITY_TYPES
    results.append(
        (
            "facility_type ⊆ {elevator, ramp, other}",
            len(unknown) == 0,
            f"unknown={unknown}" if unknown else f"types={sorted(types)}",
        )
    )

    if row_count > 0:
        other_count = hook.get_first(
            f"SELECT COUNT(*) FROM {table} WHERE facility_type = 'other'"
        )[0]
        ratio = other_count / row_count
        results.append(
            (
                f"facility_type='other' < {int(OTHER_THRESHOLD*100)}%",
                ratio < OTHER_THRESHOLD,
                f"other={other_count}/{row_count} ({ratio:.1%})",
            )
        )

    unique_stations = hook.get_first(f"SELECT COUNT(DISTINCT station) FROM {table}")[0]
    smin, smax = EXPECTED_UNIQUE_STATIONS
    results.append(
        (
            f"unique station count in [{smin}, {smax}]",
            smin <= unique_stations <= smax,
            f"actual={unique_stations}",
        )
    )

    return results
