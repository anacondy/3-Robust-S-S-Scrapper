#!/usr/bin/env python3
"""Project-to-Text Bundle Generator (Python fallback)."""

import os
import sys
from datetime import datetime
from pathlib import Path

EXCLUDE_DIRS = {
    '.git', '.github', '.idea', '.venv', '__pycache__', 'node_modules',
    'dist', 'build', 'target', 'out', '.pytest_cache', '.mypy_cache',
    '.next', '.nuxt', '.svelte-kit', '.parcel-cache', '.ruff_cache',
    'coverage', 'static', 'uploads'
}

EXCLUDE_EXTS = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.bmp',
    '.mp4', '.webm', '.mp3', '.wav', '.ogg', '.mov', '.avi', '.mkv',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip',
    '.tar', '.gz', '.rar', '.7z', '.exe', '.dll', '.so', '.dylib', '.bin',
    '.ttf', '.otf', '.woff', '.woff2', '.eot'
}

EXCLUDE_FILES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
    'Pipfile.lock', '.DS_Store', 'Thumbs.db', 'desktop.ini', 'data.json',
    'fumando-preocupado (1).gif', 'project-bundle.txt'
}


def is_excluded(path: Path, root: Path) -> bool:
    name = path.name
    ext = path.suffix.lower()
    rel_parts = path.relative_to(root).parts[:-1]  # all dirs except file

    if any(part in EXCLUDE_DIRS for part in rel_parts):
        return True
    if name in EXCLUDE_DIRS:
        return True
    if ext in EXCLUDE_EXTS:
        return True
    if name in EXCLUDE_FILES:
        return True
    return False


def main(project_dir: str, output_file: str = 'project-bundle.txt') -> None:
    root = Path(project_dir).resolve()
    files = sorted(p for p in root.rglob('*') if p.is_file() and not is_excluded(p, root))

    lines = []
    lines.append('# Project Bundle')
    lines.append(f'# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'# Root: {root}')
    lines.append(f'# Files included: {len(files)}')
    lines.append('#============================================================')
    lines.append('')

    for file in files:
        rel = file.relative_to(root).as_posix()
        lines.append(f'## FILE: {rel}')
        lines.append(f'## SIZE: {file.stat().st_size} bytes')
        lines.append('```')
        try:
            with open(file, 'r', encoding='utf-8', errors='replace') as f:
                lines.append(f.read().rstrip('\n'))
        except Exception as e:
            lines.append(f'[ERROR: Could not read file - {e}]')
        lines.append('```')
        lines.append('')

    out = Path(output_file)
    out.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Bundle written to: {out.resolve()}')
    print(f'Files included: {len(files)}')


if __name__ == '__main__':
    project_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'project-bundle.txt'
    main(project_dir, output_file)
