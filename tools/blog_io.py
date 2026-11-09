"""Shared file writing for the blog build scripts.

Some pages have mixed line endings (mostly CRLF with a few LF lines). The
scripts work on text with '\\n' and write it back with the file's own line
ending, so rewriting an unchanged page would still change its bytes and show
up in git as a line-ending-only change. write_keep_eol skips the write when
the content is the same apart from line endings.
"""
import os


def write_keep_eol(path, text, nl):
    """Write text (with '\\n' line breaks) to path using nl as the line ending.

    Returns False and leaves the file untouched if its current content is the
    same as text apart from line endings; otherwise writes it and returns True.
    """
    if os.path.isfile(path):
        old = open(path, encoding='utf-8', newline='').read()
        if old.replace('\r\n', '\n') == text.replace('\r\n', '\n'):
            return False
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    open(path, 'w', encoding='utf-8', newline='').write(text.replace('\n', nl))
    return True
