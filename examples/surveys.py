"""Run one survey test end to end: start, trigger the survey, wait, check.

Set SURVEY_CONFIG_ID to a saved survey test config and SURVEY_SENDER to the
number your survey platform sends from.
"""
import os

from nopaque import Nopaque

CONFIG_ID = os.environ["SURVEY_CONFIG_ID"]
SENDER = os.environ["SURVEY_SENDER"]   # e.g. +447921721840

with Nopaque() as client:
    run = client.surveys.start(config_id=CONFIG_ID, sender=SENDER, window_secs=600)
    print(f"Send the survey to {run.agent_e164} now (run {run.run_id}).")

    # Trigger your survey platform here, aimed at run.agent_e164.

    result = client.surveys.wait_for_result(
        run.run_id,
        on_update=lambda r: print(f"  capture={r.capture.status} answers={r.answers_given}"),
    )

    print(f"Outcome: {result.outcome} ({result.answers_given}/{result.expected_turns} answers)")
    for turn in result.turns:
        print(f"  {turn.at[11:19]} {turn.from_:<10} {turn.text}")
