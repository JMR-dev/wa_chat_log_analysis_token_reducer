import tiktoken


def count_tokens(file_path, encoding=None):
    if encoding is None:
        encoding = tiktoken.get_encoding("cl100k_base")
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return len(encoding.encode(text))
