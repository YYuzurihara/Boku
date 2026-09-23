"""The expression dictionary: JSON storage for the teacher model's
per-primitive Japanese expressions (ja_generator_plan.md "3. 承認済み表現辞
書のデータ構造").

File format -- exactly the shape ja_generator_plan.md specifies, one entry
per expression-dictionary key, top level keyed by that key:

    {
      "filter:ge_k": {"slot_type": "ADNOMINAL", "expressions": ["k以上の", ...]},
      "map:add_k":   {"slot_type": "ACTION_PAIR",
                      "expressions": [{"terminal": "kを加える", "te": "kを加えて"}, ...]},
      "frame:opening": {"slot_type": "TEXT", "expressions": ["整数リストxsから、", ...]}
    }

Provenance (model / revision / sampling / seed / prompt hash / timestamp)
deliberately does *not* live in this file: THIRD_PARTY.md puts it in the
generation log instead (``expressions/generation_log.jsonl``, written by
ja_teacher.py), which keeps the dictionary itself diffable and hand-editable
for the human approval step ("人間による表現チェック" in task_list.md).

Validation here is *structural only* -- slot shape, non-emptiness, and the
``{frag}`` placeholder that frame:filter_verb must carry. Whether an
expression is good Japanese, or preserves the operation's meaning, is the
human reviewer's call, not this module's: a weird-but-well-formed expression
must still round-trip through save/load unchanged.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any, Union

from ja_prompts import ADNOMINAL, FRAG_PLACEHOLDER, PRIMITIVES, TEXT

# An expression is a plain string (ADNOMINAL/TEXT) or a {terminal, te} pair
# (ACTION_PAIR); ja_generator.py picks the form it needs per sentence position.
Expression = Union[str, dict[str, str]]

DEFAULT_DIR = Path(__file__).resolve().parent / "expressions"
CANDIDATES_PATH = DEFAULT_DIR / "candidates.json"
APPROVED_PATH = DEFAULT_DIR / "approved.json"


class ExpressionDictionaryError(ValueError):
    """Raised when a dictionary file is structurally unusable."""


def _entry_problems(key: str, entry: Any) -> list[str]:
    """Structural problems with one entry, as human-readable strings."""
    problems: list[str] = []
    if key not in PRIMITIVES:
        return [f"{key}: unknown expression-dictionary key (not in THIRD_PARTY.md's table)"]
    if not isinstance(entry, dict):
        return [f"{key}: entry must be an object, got {type(entry).__name__}"]

    expected_slot = PRIMITIVES[key].slot_type
    slot_type = entry.get("slot_type")
    if slot_type != expected_slot:
        problems.append(f"{key}: slot_type is {slot_type!r}, expected {expected_slot!r}")

    expressions = entry.get("expressions")
    if not isinstance(expressions, list):
        problems.append(f"{key}: expressions must be a list, got {type(expressions).__name__}")
        return problems
    if not expressions:
        problems.append(f"{key}: expressions is empty (nothing to sample from)")

    for i, expr in enumerate(expressions):
        where = f"{key}[{i}]"
        if expected_slot in (ADNOMINAL, TEXT):
            if not isinstance(expr, str):
                problems.append(f"{where}: expected a string, got {type(expr).__name__}")
            elif not expr.strip():
                problems.append(f"{where}: empty string")
            continue
        # ACTION_PAIR
        if not isinstance(expr, dict):
            problems.append(f"{where}: expected a {{terminal, te}} object, got {type(expr).__name__}")
            continue
        missing = [form for form in ("terminal", "te") if not isinstance(expr.get(form), str)]
        if missing:
            problems.append(f"{where}: missing/non-string form(s): {', '.join(missing)}")
            continue
        for form in ("terminal", "te"):
            if not expr[form].strip():
                problems.append(f"{where}.{form}: empty string")
        if key == "frame:filter_verb":
            for form in ("terminal", "te"):
                count = expr[form].count(FRAG_PLACEHOLDER)
                if count != 1:
                    problems.append(
                        f"{where}.{form}: must contain the placeholder "
                        f"{FRAG_PLACEHOLDER} exactly once, found {count}"
                    )
    return problems


class ExpressionDictionary:
    """An in-memory expression dictionary, loadable from / savable to JSON.

    May be partial: a dictionary holding only some of the keys is valid
    (useful while generation is still running, or when only a few primitives
    were re-generated). ``missing_keys()`` reports what a full render would
    still need; ja_generator.py raises if it reaches a key that is absent.
    """

    def __init__(self, entries: dict[str, dict]) -> None:
        self.entries: dict[str, dict] = dict(entries)

    # -- construction --------------------------------------------------------

    @classmethod
    def from_expressions(cls, expressions_by_key: dict[str, Sequence[Expression]]) -> "ExpressionDictionary":
        """Build from raw per-key expression lists, filling in each key's
        ``slot_type`` from the primitive table (the model is never asked for
        the slot type -- it is fixed by THIRD_PARTY.md's table)."""
        entries: dict[str, dict] = {}
        for key, expressions in expressions_by_key.items():
            slot_type = PRIMITIVES[key].slot_type if key in PRIMITIVES else None
            entries[key] = {"slot_type": slot_type, "expressions": list(expressions)}
        return cls(entries)

    @classmethod
    def load(cls, path: Union[str, Path] = CANDIDATES_PATH, strict: bool = True) -> "ExpressionDictionary":
        """Read a dictionary file. With ``strict`` (the default), structural
        problems raise instead of surfacing later as a broken sentence."""
        path = Path(path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise ExpressionDictionaryError(f"expression dictionary not found: {path}") from None
        except json.JSONDecodeError as exc:
            raise ExpressionDictionaryError(f"{path} is not valid JSON: {exc}") from None
        if not isinstance(raw, dict):
            raise ExpressionDictionaryError(f"{path}: top level must be an object keyed by primitive")

        dictionary = cls(raw)
        if strict:
            problems = dictionary.validate()
            if problems:
                joined = "\n  - ".join(problems)
                raise ExpressionDictionaryError(f"{path} has structural problems:\n  - {joined}")
        return dictionary

    # -- inspection ----------------------------------------------------------

    def __contains__(self, key: object) -> bool:
        return key in self.entries

    def __len__(self) -> int:
        return len(self.entries)

    def keys(self) -> list[str]:
        """Keys in THIRD_PARTY.md table order, with any unknown keys last."""
        ordered = [k for k in PRIMITIVES if k in self.entries]
        extra = [k for k in self.entries if k not in PRIMITIVES]
        return ordered + extra

    def slot_type(self, key: str) -> str:
        return self.entry(key)["slot_type"]

    def entry(self, key: str) -> dict:
        try:
            return self.entries[key]
        except KeyError:
            raise ExpressionDictionaryError(
                f"expression dictionary has no entry for {key!r} "
                f"(have {len(self.entries)} of {len(PRIMITIVES)} keys)"
            ) from None

    def expressions(self, key: str) -> list[Expression]:
        return list(self.entry(key)["expressions"])

    def missing_keys(self) -> list[str]:
        return [key for key in PRIMITIVES if key not in self.entries]

    def counts(self) -> dict[str, int]:
        return {key: len(self.entries[key].get("expressions") or []) for key in self.keys()}

    def validate(self) -> list[str]:
        """Structural problems across all entries (empty list == usable).

        Not a judgement on the Japanese itself -- see the module docstring.
        """
        problems: list[str] = []
        for key in self.keys():
            problems.extend(_entry_problems(key, self.entries[key]))
        return problems

    def duplicate_report(self) -> dict[str, list[str]]:
        """Expressions repeated within one key. The prompts ask for 重複なし,
        so this is worth showing the human reviewer, but it is *not* an error
        and nothing is silently dropped."""
        report: dict[str, list[str]] = {}
        for key in self.keys():
            seen: set[str] = set()
            dupes: list[str] = []
            for expr in self.entries[key].get("expressions") or []:
                marker = expr if isinstance(expr, str) else json.dumps(expr, sort_keys=True, ensure_ascii=False)
                if marker in seen:
                    dupes.append(marker)
                seen.add(marker)
            if dupes:
                report[key] = dupes
        return report

    # -- serialization -------------------------------------------------------

    def to_json(self) -> str:
        """Pretty, UTF-8, table-ordered JSON -- written as-is by ``save``.
        Readable and diffable because a human edits this file during the
        approval step."""
        ordered = {key: self.entries[key] for key in self.keys()}
        return json.dumps(ordered, ensure_ascii=False, indent=2) + "\n"

    def save(self, path: Union[str, Path] = CANDIDATES_PATH) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(), encoding="utf-8")
        return path

    def content_sha256(self) -> str:
        """Stable hash of the dictionary contents, recorded on every rendered
        instruction so a saved sentence can be traced to the exact dictionary
        it was built from."""
        canonical = json.dumps(
            {key: self.entries[key] for key in self.keys()},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def merge(dictionaries: Iterable[ExpressionDictionary]) -> ExpressionDictionary:
    """Combine dictionaries, later entries winning per key (used to overlay a
    re-generated subset of primitives onto an existing file)."""
    entries: dict[str, dict] = {}
    for dictionary in dictionaries:
        entries.update(dictionary.entries)
    return ExpressionDictionary(entries)
