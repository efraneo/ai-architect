# mypy: ignore-errors
# Portado de OpenJarvis (https://github.com/openjarvis) — Apache License 2.0.
# Copyright de los autores de OpenJarvis. Archivo modificado para AI-architect (8 sep 2026):
# imports reescritos y acoplamientos a Rust/config sustituidos por piezas propias.
# La licencia completa está en ai_architect/agente/LICENCIA-OpenJarvis.txt.

"""ToolTranslator — translate external tool names to OpenJarvis equivalents.

External skill libraries (Hermes Agent, OpenClaw) reference tools by Claude
Code's standard tool names (Bash, Read, Write, etc.).  OpenJarvis uses
different names (shell_exec, file_read, file_write).  This module translates
those references in skill markdown bodies and ``allowed-tools`` fields.

The translation table is small (~10 entries) covering Claude Code's standard
tools and grows as we encounter new vendor tools.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Translation table — external name → OpenJarvis name
# ---------------------------------------------------------------------------

TOOL_TRANSLATION: dict[str, str] = {
    "Bash": "shell_exec",
    "Read": "file_read",
    "Write": "file_write",
    "Edit": "file_edit",
    "Glob": "file_glob",
    "Grep": "file_grep",
    "WebFetch": "web_search",
    "WebSearch": "web_search",
    "Task": "delegate_agent",
    "NotebookEdit": "notebook_edit",
}


class ToolTranslator:
    """Rewrite tool references in markdown bodies and allowed-tools fields.

    Uses a word-boundary regex so partial matches like 'Reader' or
    'Reading' are not rewritten.
    """

    def __init__(
        self,
        translation_table: dict[str, str] | None = None,
    ) -> None:
        self._table = dict(translation_table or TOOL_TRANSLATION)
        # Word-boundary pattern matching any external name
        names = sorted(self._table.keys(), key=len, reverse=True)
        if names:
            self._pattern = re.compile(
                r"\b(" + "|".join(re.escape(n) for n in names) + r")\b"
            )
        else:
            self._pattern = None

    def translate_markdown(self, body: str) -> tuple[str, list[str]]:
        """Translate tool references in a markdown body.

        Returns
        -------
        tuple[str, list[str]]
            (rewritten body, list of untranslated tool names found)
        """
        if not body or self._pattern is None:
            return body, []

        def _sub(match: re.Match) -> str:
            return self._table.get(match.group(1), match.group(1))

        new_body = self._pattern.sub(_sub, body)

        # Find untranslated tool-like references (CamelCase words that look
        # like tool names but aren't in the table).  Conservative heuristic:
        # words with internal uppercase (true CamelCase) followed by ' tool'
        # or a word boundary, length 3-30, not in the translation table.
        untranslated: list[str] = []
        # Require at least one uppercase letter after position 0 (true CamelCase)
        candidate_pattern = re.compile(r"\b([A-Z][a-z]+[A-Z][a-zA-Z]*)(?:\s+tool|\b)")
        for cand in candidate_pattern.findall(body):
            if cand not in self._table and cand not in untranslated:
                if 3 <= len(cand) <= 30:
                    untranslated.append(cand)
        return new_body, untranslated

    def translate_allowed_tools(self, allowed: str) -> tuple[str, list[str]]:
        """Translate the space-delimited allowed-tools field.

        Tokens may have parenthesized arguments like ``Bash(git:*)``.  Only
        the prefix before the first ``(`` is translated.
        """
        if not allowed:
            return allowed, []

        out_tokens: list[str] = []
        untranslated: list[str] = []
        for token in allowed.split():
            # Split off any (args) suffix
            if "(" in token:
                head, _, tail = token.partition("(")
                tail = "(" + tail
            else:
                head, tail = token, ""

            if head in self._table:
                out_tokens.append(self._table[head] + tail)
            else:
                out_tokens.append(token)
                if head not in untranslated:
                    untranslated.append(head)

        return " ".join(out_tokens), untranslated


__all__ = ["TOOL_TRANSLATION", "ToolTranslator"]
