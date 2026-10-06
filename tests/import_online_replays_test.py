"""Offline importer boundaries and real captured UI identity checks; no games."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools import import_online_replays as importer
from tools.audit_online import audit_ui, REASONS

ROOT = Path(__file__).resolve().parents[1]


class ImportOnlineReplaysTest(unittest.TestCase):
    def test_zip_names_selected_only_and_duplicate_download_suffix(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(root / "battle-M1-replays (1).zip", "w") as archive:
                archive.writestr("M1.replay", b"chosen")
                archive.writestr("../M2.replay", b"traversal")
                archive.writestr("folder/M2.replay", b"nested")
                archive.writestr("M99.replay", b"outside selection")
            (root / "M1 (1).replay").write_bytes(b"chosen")
            (root / "unrelated.zip").write_bytes(b"not an accepted download")
            candidates, _, issues, ignored = importer.scan_downloads(root, {1, 2})
            rows = importer.import_candidates(candidates, [1, 2], root / "output")
            self.assertEqual(len(issues), 2)
            self.assertEqual(len(ignored), 1)
            self.assertEqual(rows[0]["identical_duplicate_sources"], 1)
            self.assertEqual(rows[1]["import_status"], "missing")
            self.assertEqual((root / "output/M1.replay").read_bytes(), b"chosen")
            self.assertFalse((root / "M2.replay").exists())

    def test_conflicting_downloads_and_existing_bytes_are_never_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "M1.replay").write_bytes(b"first")
            (root / "M1 (1).replay").write_bytes(b"different")
            (root / "M2.replay").write_bytes(b"new")
            output = root / "output"
            output.mkdir()
            (output / "M2.replay").write_bytes(b"preserve")
            candidates, _, _, _ = importer.scan_downloads(root, {1, 2})
            rows = importer.import_candidates(candidates, [1, 2], output)
            self.assertEqual(rows[0]["import_status"], "conflict")
            self.assertFalse((output / "M1.replay").exists())
            self.assertEqual(rows[1]["import_status"], "conflict_with_existing_output")
            self.assertEqual((output / "M2.replay").read_bytes(), b"preserve")

    def test_zip_symlink_and_oversize_metadata_are_rejected(self):
        link = zipfile.ZipInfo("M1.replay")
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        link.file_size, link.compress_size = 5, 5
        self.assertFalse(importer.safe_flat_member(link))
        oversized = zipfile.ZipInfo("M1.replay")
        oversized.file_size = importer.MAX_REPLAY_BYTES + 1
        oversized.compress_size = oversized.file_size
        self.assertFalse(importer.safe_flat_member(oversized))

    def test_source_hash_verification_does_not_extract_or_execute_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archived = root / "archived"
            archived.mkdir()
            files = {"main.cpp": b"int main() { return 0; }", "bot.toml": b"language='cpp'"}
            for name, body in files.items():
                (archived / name).write_bytes(body)
            archive_path = root / "source.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for name, body in files.items():
                    archive.writestr(name, body)
            proof = importer.source_proof(archive_path, archived, 15719, True)
            self.assertTrue(proof["source_bytes_verified"])
            self.assertEqual(proof["source_bundle_sha256"], proof["archived_source_bundle_sha256"])
            self.assertFalse((root / "main.cpp").exists())
            with zipfile.ZipFile(root / "unsafe.zip", "w") as archive:
                archive.writestr("../main.cpp", b"outside")
            with self.assertRaises(ValueError):
                importer.source_proof(root / "unsafe.zip", archived, 15719, True)

    def test_actual_fixed_ui_maps_to_opposite_engine_side_without_parity(self):
        bundle = json.loads(gzip.decompress((ROOT / "tests/fixtures/oct6-online100-ui.json.gz").read_bytes()))
        export = next(x for x in bundle["ui_exports"] if x["match_id"] == 1230139)
        ui = audit_ui(json.loads(export["raw_json_utf8"]), {"match_id": 1230139, "our_team_id": 1035, "platform_version": 14})
        self.assertEqual(ui["our_ui_column"], "A")
        mapping = {"A": "B", "B": "A"}
        result = {"terminated": True, "endReason": ui["result"]["endReason"],
                  "winner": "B" if ui["result"]["winner"] == "A" else "A"}
        for team, column in mapping.items():
            result["team" + team] = deepcopy(ui["result"]["team" + column])
        data = {"teams": {"A": {"botId": ""}, "B": {"botId": "15719"}},
                "result": result, "seed": str(int(ui["seed"], 0)), "map": "MAP_NAME " + ui["map"]}
        core = {"initial": {"scores": {team: {"longest_dragon": 0} for team in "AB"}},
                "trajectory": [{"round": ui["last_round"] - 1, "scores": {
            team: {"longest_dragon": ui["team_longest_so_far"][column]} for team, column in mapping.items()}}]}
        detail = {"dragons": []}
        for team, column in mapping.items():
            event = next(x for x in ui["filtered_queen_events"] if x["team"] == column)
            code = next(code for code, name in REASONS.items() if name == event["reason"])
            detail["dragons"].append({"id": event["id"], "team": team, "is_queen": True,
                "death": {"round": event["round"] - 1, "reason": code}})
        audit = {"teams": {team: ui["teams"][column] for team, column in mapping.items()}}
        validated = importer.validate_ui(data, core, detail, audit, ui, 15719)
        self.assertTrue(validated["verified"], validated["issues"])
        self.assertEqual(validated["engine_team"], "B")
        data["seed"] = "1"
        self.assertFalse(importer.validate_ui(data, core, detail, audit, ui, 15719)["verified"])

    def test_map_initial_teams_and_events_are_checked(self):
        data = {"initial_dragons": [{"id": 0, "team": "B", "body": [{"x": 2, "y": 3}, {"x": 2, "y": 2}]}],
                "events": [{"type": "dragonUpdate", "id": 0, "head": {"x": 2, "y": 3}, "tail": {"x": 2, "y": 2}},
                           {"type": "roundStart", "round": 0}]}
        self.assertTrue(importer.initial_checks(data)["verified"])
        data["events"][0]["tail"]["y"] = 1
        with self.assertRaises(ValueError):
            importer.initial_checks(data)

    def test_cache_preserves_decoder_digest_and_skips_reconstruction(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "M1.replay"
            path.write_bytes(b"raw bytes")
            proof = {"source_bytes_verified": False}
            provenance = {"replay_sha256": importer.sha(b"raw bytes"), "ui_sha256": "ui",
                          "source_zip_sha256": None, "source_bundle_sha256": None,
                          "source_bytes_verified": False, "dependencies": {"audit_online.py": "digest"},
                          "decoder_bundle_sha256": "actual official decoder digest"}
            importer.write_json(path.with_suffix(".analysis.json"), {"provenance": provenance})
            with patch.object(importer, "load_replay", side_effect=AssertionError("should use cache")):
                _, cached = importer.analyze_one(path, {"input_sha256": "ui"}, {}, proof, 15719,
                                                 {"audit_online.py": "digest"})
            self.assertTrue(cached)


if __name__ == "__main__":
    unittest.main()
