import json
from pathlib import Path
import tempfile
import unittest

from components.shared.project_lifecycle import (
    ProjectLifecycle,
    RecentFilesStore,
    atomic_write_json,
)


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


if __name__ == "__main__":
    unittest.main()
