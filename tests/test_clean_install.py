import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_SMOKE_TEST = r"""
import sqlite3
from html.parser import HTMLParser
from pathlib import Path

connection = sqlite3.connect("getfit.db")
connection.executescript(Path("sql.txt").read_text(encoding="utf-8"))
connection.close()

from app import app

app.config.update(TESTING=True)
client = app.test_client()
registration = client.post(
    "/register",
    data={
        "username": "clean-install-user",
        "password": "clean-install-password",
        "confirmation": "clean-install-password",
    },
)
assert registration.status_code in (302, 303), registration.status_code

login = client.post(
    "/login",
    data={"username": "clean-install-user", "password": "clean-install-password"},
)
assert login.status_code in (302, 303), login.status_code

dashboard = client.get("/dashboard")
assert dashboard.status_code == 200, dashboard.status_code
dashboard_html = dashboard.get_data(as_text=True)

class ModalNestingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.inside_dashboard = {}

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        modal_id = attributes.get("id")
        if modal_id in {"calorieTargetModal", "calorieIntakeModal"}:
            self.inside_dashboard[modal_id] = any(
                "dashboard-page" in (parent.get("class") or "").split()
                for _, parent in self.stack
            )
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append((tag, attributes))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

parser = ModalNestingParser()
parser.feed(dashboard_html)
assert parser.inside_dashboard == {
    "calorieTargetModal": False,
    "calorieIntakeModal": False,
}, parser.inside_dashboard

target_save = client.post("/calorie-target", data={"calorie_target": "2200"})
assert target_save.status_code in (302, 303), target_save.status_code
dashboard_html = client.get("/dashboard").get_data(as_text=True)
assert "/ 2200 kcal" in dashboard_html

intake_save = client.post(
    "/calorie-intake",
    data={"action": "adjust", "calories": "1234"},
)
assert intake_save.status_code in (302, 303), intake_save.status_code
dashboard_html = client.get("/dashboard").get_data(as_text=True)
assert "1234" in dashboard_html
"""


class CleanInstallSmokeTests(unittest.TestCase):
    def test_new_database_can_register_log_in_and_render_dashboard(self):
        with tempfile.TemporaryDirectory(prefix="getfit-clean-install-") as temp:
            project = Path(temp)
            for filename in ("app.py", "quotes.json", "sql.txt"):
                shutil.copy2(PROJECT_ROOT / filename, project / filename)
            shutil.copytree(PROJECT_ROOT / "templates", project / "templates")
            static = project / "static"
            static.mkdir()
            for filename in ("style.css", "script.js", "w.png"):
                shutil.copy2(PROJECT_ROOT / "static" / filename, static / filename)

            environment = os.environ.copy()
            environment["SECRET_KEY"] = "clean-install-test-secret"
            result = subprocess.run(
                [sys.executable, "-c", APP_SMOKE_TEST],
                cwd=project,
                env=environment,
                capture_output=True,
                text=True,
                timeout=30,
            )

            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
