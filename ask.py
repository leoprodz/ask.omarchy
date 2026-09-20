#!/usr/bin/python3
"""Map natural language to the three most likely Omarchy shortcuts via Jev. Show them; do not run them."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

JEV_URL = "https://api.typesafe.ai/v1/systemone"
JEV_MODEL = "jev-latest"
SECRET_FILES = (Path.home() / ".vault" / ".env.master",)
TOP_N = 3


def dotenv_value(path: Path, names: set[str]) -> str:
  if not path.is_file():
    return ""
  for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
      continue
    if line.startswith("export "):
      line = line[7:].strip()
    name, value = line.split("=", 1)
    if name.strip() in names:
      found = value.strip().strip("'\"")
      if found:
        return found
  return ""


def load_key() -> str:
  key = os.environ.get("TYPESAFE_API_KEY") or os.environ.get("JEV_API_KEY") or ""
  if key.strip():
    return key.strip()
  for path in SECRET_FILES:
    found = dotenv_value(path, {"TYPESAFE_API_KEY", "JEV_API_KEY"})
    if found:
      return found
  return ""


def notify(title: str, body: str = "") -> None:
  cmd = ["omarchy-notification-send", "-g", "󰍉", title]
  if body:
    cmd.append(body)
  subprocess.run(cmd, check=False)


def menu_input(prompt: str) -> str:
  selection_file = Path(tempfile.mkstemp(prefix="omarchy-ask-")[1])
  done_file = Path(tempfile.mkstemp(prefix="omarchy-ask-done-")[1])
  selection_file.write_text("", encoding="utf-8")
  done_file.unlink(missing_ok=True)
  payload = json.dumps(
    {
      "prompt": prompt,
      "selectionFile": str(selection_file),
      "doneFile": str(done_file),
    }
  )
  summoned = subprocess.run(
    ["omarchy-shell", "shell", "summon", "leo.ask", payload],
    capture_output=True,
    text=True,
  )
  if summoned.returncode != 0:
    result = subprocess.run(
      ["omarchy-menu-input", prompt, "--width", "800"],
      capture_output=True,
      text=True,
    )
    if result.returncode != 0:
      sys.exit(1)
    return result.stdout.strip()

  while not done_file.exists():
    time.sleep(0.05)
  text = selection_file.read_text(encoding="utf-8").strip() if selection_file.is_file() else ""
  selection_file.unlink(missing_ok=True)
  done_file.unlink(missing_ok=True)
  if not text:
    sys.exit(1)
  return text


def menu_select(prompt: str, options: list[str]) -> str:
  proc = subprocess.run(
    ["omarchy-menu-select", prompt, "--", "--width", "800", "--maxheight", "400"],
    input="\n".join(options) + "\n",
    capture_output=True,
    text=True,
  )
  if proc.returncode != 0:
    sys.exit(1)
  return proc.stdout.strip()


def keybindings() -> list[dict[str, str]]:
  raw = subprocess.check_output(["omarchy", "menu", "keybindings", "--print"], text=True)
  rows: list[dict[str, str]] = []
  for line in raw.splitlines():
    if "→" not in line:
      continue
    chord, action = line.split("→", 1)
    chord, action = chord.strip(), action.strip()
    if chord and action:
      rows.append({"chord": chord, "action": action})
  return rows


def slug(text: str, used: set[str]) -> str:
  chars = []
  for ch in text.lower():
    chars.append(ch if ch.isalnum() else "_")
  compact = "".join(chars).strip("_")
  while "__" in compact:
    compact = compact.replace("__", "_")
  base = ("k_" + (compact or "x"))[:48]
  candidate = base
  n = 2
  while candidate in used:
    suffix = f"_{n}"
    candidate = base[: 48 - len(suffix)] + suffix
    n += 1
  used.add(candidate)
  return candidate


def jev_ranked(key: str, state: str, instructions: str, criteria: dict[str, str]) -> list[tuple[str, float]]:
  body = {
    "model": JEV_MODEL,
    "state": state,
    "questions": {
      "pick": {
        "type": "choice",
        "instructions": instructions,
        "criteria": criteria,
      }
    },
  }
  req = urllib.request.Request(
    JEV_URL,
    data=json.dumps(body).encode("utf-8"),
    method="POST",
    headers={
      "Authorization": "Bearer " + key,
      "Content-Type": "application/json",
    },
  )
  try:
    with urllib.request.urlopen(req, timeout=30) as resp:
      payload = json.loads(resp.read().decode("utf-8", errors="replace"))
  except urllib.error.HTTPError as error:
    detail = error.read().decode("utf-8", errors="replace")[:240]
    raise RuntimeError(f"Jev HTTP {error.code}: {detail}") from error
  except Exception as error:
    raise RuntimeError(f"Jev request failed: {error}") from error

  answers = payload.get("answers") or {}
  pick = answers.get("pick") if isinstance(answers, dict) else None
  if not isinstance(pick, dict):
    raise RuntimeError("Jev returned no choice")

  ranked: list[tuple[str, float]] = []
  probs = pick.get("probabilities")
  if isinstance(probs, dict) and probs:
    for name, value in probs.items():
      try:
        ranked.append((str(name), float(value)))
      except (TypeError, ValueError):
        continue
    ranked.sort(key=lambda item: item[1], reverse=True)
  elif pick.get("choice"):
    ranked = [(str(pick["choice"]), 1.0)]
  if not ranked:
    raise RuntimeError("Jev returned no choice")
  return ranked


def copy_text(text: str) -> None:
  subprocess.run(["wl-copy"], input=text, text=True, check=False)


def main() -> int:
  query = " ".join(sys.argv[1:]).strip() or menu_input("What do you want to do?")
  if not query:
    return 1

  key = load_key()
  if not key:
    notify(
      "Jev API key missing",
      "Run omarchy-vault-pull, or put TYPESAFE_API_KEY in ~/.vault/.env.master",
    )
    return 1

  rows = keybindings()
  if not rows:
    notify("No keybindings found")
    return 1

  used: set[str] = set()
  by_id: dict[str, dict[str, str]] = {}
  criteria: dict[str, str] = {}
  for row in rows[:255]:
    sid = slug(row["action"] + " " + row["chord"], used)
    by_id[sid] = row
    criteria[sid] = f"{row['action']} (shortcut {row['chord']})"

  try:
    ranked = jev_ranked(
      key,
      query,
      "Which Omarchy keyboard shortcuts best match this request? Rank every option.",
      criteria,
    )
  except RuntimeError as error:
    notify("Jev could not pick shortcuts", str(error))
    return 1

  picked: list[dict[str, str]] = []
  seen: set[str] = set()
  for sid, _prob in ranked:
    row = by_id.get(sid)
    if row is None:
      continue
    marker = row["chord"] + "\0" + row["action"]
    if marker in seen:
      continue
    seen.add(marker)
    picked.append(row)
    if len(picked) >= TOP_N:
      break

  if not picked:
    notify("Jev picked unknown shortcuts")
    return 1

  copy_text(picked[0]["chord"])
  options = [f"󰌌\t{row['chord']}\t{row['action']}" for row in picked]
  selected = menu_select("Most likely shortcuts (not run)", options)
  chord = selected.split("\t", 1)[0].strip() if selected else picked[0]["chord"]
  if chord:
    copy_text(chord)
  notify("Shortcut copied", chord or picked[0]["chord"])
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
