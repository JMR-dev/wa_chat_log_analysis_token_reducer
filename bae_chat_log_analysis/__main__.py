import argparse
import cProfile
import io
import pstats
import time
from pathlib import Path

import tiktoken

from .abbreviations import generate_emoji_abbreviations
from .reducer import reduce_tokens

_DEFAULT_SOURCE = Path("bae_chat_logs/Source/WhatsApp_Bae_Chat.txt")
_DEFAULT_OUTPUT = Path("bae_chat_logs/Reduced/WhatsApp_Chat-08-03-2026-reduced")

def _fmt(seconds):
    return f"{seconds * 1000:.1f}ms" if seconds < 1 else f"{seconds:.2f}s"


def main(source_file=_DEFAULT_SOURCE, output_file=_DEFAULT_OUTPUT, split_by="month"):
    print()

    t_total = time.perf_counter()

    # 1. Generate abbreviations
    print("Generating emoji abbreviations...")
    t0 = time.perf_counter()
    abbreviations = generate_emoji_abbreviations()
    print(f"  {len(abbreviations)} abbreviations loaded  [{_fmt(time.perf_counter() - t0)}]")

    # 2. Reduce source file (token counts come back from in-memory content — no re-reads)
    print(f"Reducing {source_file} (split by: {split_by})...")
    t0 = time.perf_counter()
    encoding = tiktoken.get_encoding("cl100k_base")
    output_files, reduced_tokens_total, source_tokens = reduce_tokens(
        source_file, output_file, abbreviations, split_by, encoding=encoding
    )
    print(f"  Reduction complete  [{_fmt(time.perf_counter() - t0)}]")
    for f in output_files:
        print(f"  Saved to {f}")

    saved = source_tokens - reduced_tokens_total

    print()
    print(f"Source tokens:  {source_tokens:,}")
    print(f"Reduced tokens: {reduced_tokens_total:,}")
    print(f"Tokens saved:   {saved:,} ({saved / source_tokens * 100:.1f}%)")
    print(f"\nTotal time: {_fmt(time.perf_counter() - t_total)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", type=Path, default=_DEFAULT_SOURCE,
                        help="Source chat log file (default: %(default)s)")
    parser.add_argument("output", nargs="?", type=Path, default=_DEFAULT_OUTPUT,
                        help="Output file base path (default: %(default)s)")
    parser.add_argument(
        "--split",
        choices=["year", "month", "week", "day", "none"],
        default="none",
        help="How to split the chat output (default: %(default)s)",
    )
    parser.add_argument(
        "--profile",
        nargs="?",
        const=20,
        type=int,
        metavar="N",
        help="Run with cProfile and print the top N functions by cumulative time (default: 20)",
    )
    args = parser.parse_args()

    if args.profile:
        pr = cProfile.Profile()
        pr.enable()
        main(args.source, args.output, args.split)
        pr.disable()
        buf = io.StringIO()
        ps = pstats.Stats(pr, stream=buf).sort_stats(pstats.SortKey.CUMULATIVE)
        ps.print_stats(args.profile)
        print("\n--- cProfile output ---")
        print(buf.getvalue())
    else:
        main(args.source, args.output, args.split)
