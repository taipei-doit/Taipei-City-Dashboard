"""
DAG-specific verification for mrt_a11y_alert.

Tests business logic that the generic verifier cannot know:
- station should not have「站」suffix (proves the .str.replace happened)
- status values are constrained to {active, closed}
- line column is non-empty
"""


def verify(hook, config):
    """
    Args:
        hook: Airflow PostgresHook bound to ready_data DB
        config: dict from job_config.json["dag_infos"]
    Returns:
        list of (name, ok, detail)
    """
    results = []
    table = config["ready_data_default_table"]

    bad_status = hook.get_first(
        f"SELECT COUNT(*) FROM {table} "
        f"WHERE status NOT IN ('active', 'closed') OR status IS NULL"
    )[0]
    results.append(
        (
            "status in {active, closed}",
            bad_status == 0,
            f"out-of-set rows={bad_status}",
        )
    )

    suffix_violations = hook.get_first(
        f"SELECT COUNT(*) FROM {table} WHERE station LIKE '%站'"
    )[0]
    results.append(
        (
            "station has no '站' suffix",
            suffix_violations == 0,
            f"violation rows={suffix_violations}",
        )
    )

    null_line = hook.get_first(
        f"SELECT COUNT(*) FROM {table} WHERE line IS NULL OR line = ''"
    )[0]
    results.append(
        (
            "line non-empty",
            null_line == 0,
            f"null/empty rows={null_line}",
        )
    )

    return results
