#!/usr/bin/env python3
"""Summarize log snippets and map them to predefined corrective actions."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_actions(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def choose_action(snippet: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    for action in actions:
        pattern = action.get("pattern")
        if not pattern:
            continue
        try:
            if re.search(pattern, snippet, flags=re.IGNORECASE | re.MULTILINE):
                return action
        except re.error:
            continue
    return {
        "pattern": "generic",
        "label": "Sem correspondência",
        "summary": "Uso do fallback genérico. Ajuste docs/error_actions.json para ampliar cobertura.",
        "command": "code logs/last_error_report.md",
        "notes": [
            "Nenhuma ação conhecida foi encontrada para este erro.",
            "Revise o snippet abaixo e atualize o mapeamento de ações."
        ],
    }


def build_report(
    *,
    source: str,
    trigger_line: str,
    snippet: str,
    action: Dict[str, Any],
    report_path: Path,
) -> None:
    timestamp = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    summary = action.get("summary", "Resumo indisponível.")
    command = action.get("command", "")
    label = action.get("label", action.get("pattern", "sem rótulo"))
    notes = action.get("notes", [])

    lines: List[str] = []
    lines.append(f"# Error report ({timestamp})")
    lines.append("")
    lines.append(f"- Source: {source}")
    lines.append(f"- Trigger: {trigger_line.strip() if trigger_line else 'n/a'}")
    lines.append(f"- Signature: {label}")
    lines.append(f"- Summary: {summary}")
    if command:
        lines.append(f"- Suggested command: `{command}`")
    lines.append("")

    if notes:
        lines.append("## Notes")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.append("## Log snippet")
    lines.append("```")
    lines.append(snippet.rstrip())
    lines.append("```")
    lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def tail_snippet(snippet_path: Path, max_lines: int) -> str:
    text = snippet_path.read_text(encoding="utf-8", errors="replace")
    all_lines = text.splitlines()
    if len(all_lines) <= max_lines:
        return "\n".join(all_lines)
    return "\n".join(all_lines[-max_lines:])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resume erro e sugira ação.")
    parser.add_argument("--source", required=True, help="Arquivo/log monitorado.")
    parser.add_argument("--snippet", required=True, help="Caminho do snippet temporário.")
    parser.add_argument("--actions", default="docs/error_actions.json", help="Mapa de ações em JSON.")
    parser.add_argument("--report", default="logs/last_error_report.md", help="Arquivo Markdown de saída.")
    parser.add_argument("--trigger-line", default="", help="Linha que disparou o monitor.")
    parser.add_argument("--max-lines", type=int, default=120, help="Número máximo de linhas a manter no snippet.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snippet_path = Path(args.snippet)
    report_path = Path(args.report)
    actions_path = Path(args.actions)

    snippet = tail_snippet(snippet_path, args.max_lines)
    actions = load_actions(actions_path)
    action = choose_action(snippet, actions)

    build_report(
        source=args.source,
        trigger_line=args.trigger_line,
        snippet=snippet,
        action=action,
        report_path=report_path,
    )

    suggested = action.get("command", "")
    if suggested:
        print(f"[sentinel] Suggested command: {suggested}")
    print(f"[sentinel] Report updated: {report_path}")


if __name__ == "__main__":
    main()
