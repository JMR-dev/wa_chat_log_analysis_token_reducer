import re
from collections import defaultdict
from datetime import date
from pathlib import Path

import ahocorasick
import emoji

_NAME_REPLACEMENTS = {
    'Honeybelle Ong-Jimenez Gaitano': 'Belle',
    'Jason Ross': 'Jason',
}


def _build_automaton(abbreviations):
    """Build an Aho-Corasick automaton for name and multi-codepoint emoji replacements.

    Single-codepoint emoji are handled separately via str.translate() (_build_translate_table),
    which is a pure-C O(n) pass and much faster for high-frequency single chars.
    Abbreviation strings (':long_name:' -> ':short:') are omitted — they were only needed
    as a second pass after emoji.demojize(), which we no longer call.
    """
    A = ahocorasick.Automaton()
    for long, short in _NAME_REPLACEMENTS.items():
        A.add_word(long, (len(long), short))
    for char, meta in emoji.EMOJI_DATA.items():
        if len(char) > 1:
            en_name = meta['en']
            target = abbreviations.get(en_name, en_name)
            A.add_word(char, (len(char), target))
    if len(A) == 0:
        return None
    A.make_automaton()
    return A


def _build_translate_table(abbreviations):
    """Build a str.translate() table for single-codepoint emoji.

    Must be applied AFTER the automaton pass so that multi-codepoint emoji (e.g. 👋🏻)
    are consumed first, leaving only standalone single-codepoint occurrences.
    """
    table = {}
    for char, meta in emoji.EMOJI_DATA.items():
        if len(char) == 1:
            en_name = meta['en']
            table[ord(char)] = abbreviations.get(en_name, en_name)
    return table


def _apply_automaton(text, automaton):
    """Single-pass replacement using Aho-Corasick (left-to-right, longest match wins)."""
    # Keep only the longest match per start position to avoid sorting dominated matches.
    # Composite emoji (e.g. 👋🏻) generate overlapping matches at the same start;
    # the dict ensures only the longest is retained before we sort start positions.
    best = {}
    for end_idx, (pat_len, replacement) in automaton.iter(text):
        start = end_idx - pat_len + 1
        end = end_idx + 1
        existing = best.get(start)
        if existing is None or end > existing[0]:
            best[start] = (end, replacement)

    parts = []
    last_end = 0
    for start in sorted(best):
        end, replacement = best[start]
        if start < last_end:
            continue  # overlapping with a previously committed match — skip
        parts.append(text[last_end:start])
        parts.append(replacement)
        last_end = end
    parts.append(text[last_end:])
    return ''.join(parts)


_DATE_RE = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{2,4}),')


def _date_key(month, day, year_short, split_by):
    year = 2000 + int(year_short) if int(year_short) < 100 else int(year_short)
    if split_by == 'year':
        return str(year)
    elif split_by == 'month':
        return f"{year}-{int(month):02d}"
    elif split_by == 'week':
        iso_year, iso_week, _ = date(year, int(month), int(day)).isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    else:  # day
        return f"{year}-{int(month):02d}-{int(day):02d}"


def _reduce_line(line, automaton, translate_table):
    if automaton is not None:
        line = _apply_automaton(line, automaton)
    return line.translate(translate_table)


def reduce_tokens(input_file, output_file, abbreviations, split_by='none', encoding=None):
    """Replace long usernames and convert emojis to shortened text codes.

    split_by: 'none', 'year', 'month', 'week', or 'day'
    encoding: optional tiktoken encoding; if provided, token counts are computed with
              two encode calls total (source + all reduced) — no re-reads needed.
    Returns (list[Path], int, int) — output paths, total reduced token count,
    and source token count. Token counts are -1 when encoding is None.
    """
    output_file = Path(output_file)
    if output_file.suffix != '.txt':
        output_file = output_file.with_suffix(output_file.suffix + '.txt')

    automaton = _build_automaton(abbreviations)
    translate_table = _build_translate_table(abbreviations)

    with open(input_file, 'r', encoding='utf-8') as f_in:
        source_text = f_in.read()

    source_tokens = len(encoding.encode(source_text)) if encoding is not None else -1

    if split_by == 'none':
        reduced = _reduce_line(source_text, automaton, translate_table)
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.write(reduced)
        reduced_tokens = len(encoding.encode(reduced)) if encoding is not None else -1
        return [Path(output_file)], reduced_tokens, source_tokens

    # Split mode: group lines by date bucket
    buckets = defaultdict(list)
    current_key = None

    for line in source_text.splitlines(keepends=True):
        reduced = _reduce_line(line, automaton, translate_table)
        match = _DATE_RE.match(reduced)
        if match:
            month, day, year_short = match.groups()
            current_key = _date_key(month, day, year_short, split_by)
        if current_key is None:
            current_key = '_unknown'
        buckets[current_key].append(reduced)

    output_path = Path(output_file)
    stem = output_path.stem if output_path.suffix else output_path.name
    parent = output_path.parent
    suffix = output_path.suffix or ''

    written_files = []
    for key in sorted(buckets):
        content = ''.join(buckets[key])
        out = parent / f"{stem}-{key}{suffix}"
        with open(out, 'w', encoding='utf-8') as f_out:
            f_out.write(content)
        written_files.append(out)

    all_reduced = ''.join(''.join(lines) for lines in buckets.values())
    reduced_tokens = len(encoding.encode(all_reduced)) if encoding is not None else -1

    return written_files, reduced_tokens, source_tokens
