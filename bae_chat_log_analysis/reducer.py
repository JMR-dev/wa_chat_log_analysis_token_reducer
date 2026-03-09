import re
from collections import defaultdict
from pathlib import Path

import emoji


def _reduce_line(line, abbreviations):
    """Apply all token reductions to a single line."""
    line = line.replace('Honeybelle Ong-Jimenez Gaitano', 'Belle')
    line = line.replace('Jason Ross', 'Jason')
    line = emoji.demojize(line)
    for long, short in abbreviations.items():
        line = line.replace(long, short)
    return line


_DATE_RE = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{2,4}),')


def _date_key(month, day, year_short, split_by):
    year = 2000 + int(year_short) if int(year_short) < 100 else int(year_short)
    if split_by == 'year':
        return str(year)
    elif split_by == 'month':
        return f"{year}-{int(month):02d}"
    else:  # day
        return f"{year}-{int(month):02d}-{int(day):02d}"


def reduce_tokens(input_file, output_file, abbreviations, split_by='none'):
    """Replace long usernames and convert emojis to shortened text codes.

    split_by: 'none', 'year', 'month', or 'day'
    Returns a list of output file paths that were written.
    """
    output_file = Path(output_file)
    if output_file.suffix != '.txt':
        output_file = output_file.with_suffix(output_file.suffix + '.txt')

    if split_by == 'none':
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            for line in f_in:
                f_out.write(_reduce_line(line, abbreviations))
        return [Path(output_file)]

    # Split mode: group lines by date bucket
    buckets = defaultdict(list)
    current_key = None

    with open(input_file, 'r', encoding='utf-8') as f_in:
        for line in f_in:
            match = _DATE_RE.match(line)
            if match:
                month, day, year_short = match.groups()
                current_key = _date_key(month, day, year_short, split_by)
            reduced = _reduce_line(line, abbreviations)
            if current_key is None:
                current_key = '_unknown'
            buckets[current_key].append(reduced)

    output_path = Path(output_file)
    stem = output_path.stem if output_path.suffix else output_path.name
    parent = output_path.parent
    suffix = output_path.suffix or ''

    written_files = []
    for key in sorted(buckets):
        out = parent / f"{stem}-{key}{suffix}"
        with open(out, 'w', encoding='utf-8') as f_out:
            f_out.writelines(buckets[key])
        written_files.append(out)

    return written_files
