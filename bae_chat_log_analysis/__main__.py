from pathlib import Path

from .abbreviations import generate_emoji_abbreviations
from .reducer import reduce_tokens
from .token_counter import count_tokens

SOURCE_FILE = Path("bae_chat_logs/Source/WhatsApp_Bae_Chat.txt")
REDUCED_FILE = Path("bae_chat_logs/Reduced/WhatsApp_Chat-08-03-2026-reduced")

SPLIT_OPTIONS = {'1': 'year', '2': 'month', '3': 'day', '4': 'none'}


def prompt_split_option():
    print("How would you like to split the chat output?")
    print("  1) By year")
    print("  2) By month")
    print("  3) By day")
    print("  4) No split (single file)")
    while True:
        choice = input("Enter choice (1-4): ").strip()
        if choice in SPLIT_OPTIONS:
            return SPLIT_OPTIONS[choice]
        print("Invalid choice. Please enter 1, 2, 3, or 4.")


def main():
    split_by = prompt_split_option()
    print()

    # 1. Generate abbreviations
    print("Generating emoji abbreviations...")
    abbreviations = generate_emoji_abbreviations()
    print(f"  {len(abbreviations)} abbreviations loaded")

    # 2. Reduce source file
    print(f"Reducing {SOURCE_FILE} (split by: {split_by})...")
    output_files = reduce_tokens(SOURCE_FILE, REDUCED_FILE, abbreviations, split_by)
    for f in output_files:
        print(f"  Saved to {f}")

    # 3. Count and display tokens
    print("Counting tokens...")
    source_tokens = count_tokens(SOURCE_FILE)

    reduced_tokens_total = 0
    for f in output_files:
        tokens = count_tokens(f)
        reduced_tokens_total += tokens
        if len(output_files) > 1:
            print(f"  {f.name}: {tokens:,} tokens")

    saved = source_tokens - reduced_tokens_total

    print()
    print(f"Source tokens:  {source_tokens:,}")
    print(f"Reduced tokens: {reduced_tokens_total:,}")
    print(f"Tokens saved:   {saved:,} ({saved / source_tokens * 100:.1f}%)")


if __name__ == "__main__":
    main()
