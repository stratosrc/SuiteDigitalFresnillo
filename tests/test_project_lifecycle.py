import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from components.shared.project_lifecycle import (
    ProjectLifecycle,
    RecentFilesStore,
    atomic_write_json,
)
from components.shared.protected_storage import unprotect_bytes
from components.shared.protected_storage import protect_bytes


class ProjectLifecycleTests(unittest.TestCase):
    def test_atomic_json_replaces_target(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "project.json"
            atomic_write_json(target, {"value": 1})
            atomic_write_json(target, {"value": 2})
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"value": 2})
            self.assertEqual(list(target.parent.glob("*.tmp")), [])

    def test_dirty_state_returns_to_clean_after_save(self):
        state = {"value": 1}
        lifecycle = ProjectLifecycle(
            "test",
            snapshot=lambda: dict(state),
            save=lambda: True,
        )
        self.assertFalse(lifecycle.is_dirty)
        state["value"] = 2
        self.assertTrue(lifecycle.is_dirty)
        lifecycle.mark_saved()
        self.assertFalse(lifecycle.is_dirty)

    def test_recent_files_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first = Path(temp_dir) / "one.og"
            second = Path(temp_dir) / "two.og"
            first.write_text("1", encoding="utf-8")
            second.write_text("2", encoding="utf-8")
            store = RecentFilesStore("unit-test")
            store.path = Path(temp_dir) / "recent.json"
            store.add(first)
            store.add(second)
            store.add(first)
            self.assertEqual(store.list(), [first.resolve(), second.resolve()])

    def test_autosave_writes_dirty_snapshot_and_mark_saved_clears_it(self):
        state = {"value": 1}
        lifecycle = ProjectLifecycle(
            "autosave-test",
            snapshot=lambda: dict(state),
            save=lambda: True,
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            lifecycle.recovery_path = Path(temp_dir) / "recovery.bin"
            state["value"] = 2
            lifecycle._autosave_tick()

            payload = json.loads(
                unprotect_bytes(lifecycle.recovery_path.read_bytes()).decode("utf-8")
            )
            self.assertEqual(payload["snapshot"], {"value": 2})

            lifecycle.mark_saved()
            self.assertFalse(lifecycle.recovery_path.exists())

    def test_recent_file_failure_does_not_make_mark_saved_fail(self):
        state = {"value": 2}
        lifecycle = ProjectLifecycle(
            "recent-failure-test",
            snapshot=lambda: dict(state),
            save=lambda: True,
        )
        lifecycle.recent_files.add = lambda _path: (_ for _ in ()).throw(
            PermissionError("denied")
        )

        lifecycle.mark_saved(Path("project.og"))

        self.assertFalse(lifecycle.is_dirty)

    def test_confirmation_supports_save_discard_and_cancel(self):
        state = {"value": 1}
        save_calls = []
        lifecycle = ProjectLifecycle(
            "confirmation-test",
            snapshot=lambda: dict(state),
            save=lambda: save_calls.append(True) or lifecycle.mark_saved() or True,
        )
        state["value"] = 2

        with patch(
            "components.shared.project_lifecycle.ask_save_discard_cancel",
            return_value="cancel",
        ):
            self.assertFalse(lifecycle.confirm_discard(None))
        with patch(
            "components.shared.project_lifecycle.ask_save_discard_cancel",
            return_value="discard",
        ):
            self.assertTrue(lifecycle.confirm_discard(None))
        with patch(
            "components.shared.project_lifecycle.ask_save_discard_cancel",
            return_value="save",
        ):
            self.assertTrue(lifecycle.confirm_discard(None))
        self.assertEqual(save_calls, [True])

    def test_recovery_restores_encrypted_snapshot_after_confirmation(self):
        lifecycle = ProjectLifecycle(
            "recovery-test",
            snapshot=lambda: {},
            save=lambda: True,
        )
        restored = []
        with tempfile.TemporaryDirectory() as temp_dir:
            lifecycle.recovery_dir = Path(temp_dir)
            lifecycle.recovery_path = Path(temp_dir) / "recovery.bin"
            payload = {
                "snapshot": {"value": 7},
                "path": str(Path(temp_dir) / "project.og"),
            }
            lifecycle.recovery_path.write_bytes(
                protect_bytes(json.dumps(payload).encode("utf-8"))
            )
            with patch(
                "components.shared.project_lifecycle.messagebox.askyesno",
                return_value=True,
            ):
                recovered = lifecycle.offer_recovery(
                    None,
                    lambda snapshot, path: restored.append((snapshot, path)),
                )

        self.assertTrue(recovered)
        self.assertEqual(restored[0][0], {"value": 7})
        self.assertEqual(restored[0][1].name, "project.og")


if __name__ == "__main__":
    unittest.main()
