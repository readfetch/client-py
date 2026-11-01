import json
import unittest
from pathlib import Path

from typing import Optional

from readfetch_client.endpoints import BY_NAME, CATALOG_ENDPOINTS, INTEGRATOR_ENDPOINTS


def _catalog_path() -> Optional[Path]:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "catalog.json"
        if candidate.is_file():
            return candidate
    return None


class CatalogSyncTest(unittest.TestCase):
    def test_matches_published_catalog(self) -> None:
        path = _catalog_path()
        if path is None:
            self.skipTest("catalog.json not in tree")
        catalog = json.loads(path.read_text())
        published = [e for e in catalog["endpoints"] if e.get("published")]
        self.assertEqual(len(CATALOG_ENDPOINTS), len(published))
        for spec in published:
            ours = next(e for e in CATALOG_ENDPOINTS if e.name == spec["name"])
            self.assertEqual(ours.path, spec["path"])
            self.assertEqual(ours.method, spec.get("method", "POST"))
            self.assertEqual(ours.free, bool(spec.get("free")))
        self.assertEqual(len(INTEGRATOR_ENDPOINTS), 2)
        self.assertIn("feedback", BY_NAME)
        self.assertIn("claims", BY_NAME)


if __name__ == "__main__":
    unittest.main()
