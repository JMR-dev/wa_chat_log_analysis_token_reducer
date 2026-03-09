import ast
from pathlib import Path

ABBREVIATIONS_FILE = Path(__file__).resolve().parent.parent / "abbreviations.txt"


def generate_emoji_abbreviations():
    """Load emoji abbreviation mappings from abbreviations.txt."""
    text = ABBREVIATIONS_FILE.read_text(encoding="utf-8")
    # The file contains "EMOJI_ABBREVIATIONS = { ... }" — extract the dict literal
    _, _, dict_literal = text.partition("=")
    return ast.literal_eval(dict_literal.strip())
