"""Bind KGTS discovery records without changing the original evidence collector.

Only strict read_plan/candidate_record/status providers differ. The shared
collector still verifies each result, map, external identity and replay digest.
This does not run games, infer bot-specific WASM, or promote any candidate.
"""
import oct7_build_manifest as collector
import oct7_kgts_panel as kgts_driver


if __name__ == "__main__":
    collector.panel_driver = kgts_driver
    collector.__file__ = __file__
    collector.main()
