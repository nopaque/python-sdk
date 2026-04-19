"""Create a mapping job, start it, wait until it terminates, print tree stats."""
import os

from nopaque import Nopaque

PHONE_NUMBER = os.environ["TARGET_PHONE_NUMBER"]   # e.g. +441234567890

with Nopaque() as client:
    job = client.mapping.create(
        name="Demo mapping",
        phone_number=PHONE_NUMBER,
        mapping_mode="dtmf",
    )
    print(f"Created job {job.id}")

    client.mapping.start(job.id)
    print("Started run; waiting for completion...")

    final = client.mapping.wait_for_complete(
        job.id,
        timeout=900.0,
        on_update=lambda j: print(f"  status={j.status}"),
    )
    print(f"Final status: {final.status}")

    tree = client.mapping.tree(job.id)
    if tree.stats:
        s = tree.stats
        print(
            f"Total calls: {s.total_calls} "
            f"(completed={s.completed_calls}, failed={s.failed_calls}, "
            f"loops={s.loops_detected})"
        )
