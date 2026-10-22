"""Expose pinned Western Europe registers through the regional CLI."""
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import western_europe_sources


def main():
    if '--data-root' not in sys.argv and os.environ.get('WORLD_LOCALITIES_ADDRESS_ROOT'):
        sys.argv.extend(['--data-root', os.environ['WORLD_LOCALITIES_ADDRESS_ROOT']])
    western_europe_sources.main()


if __name__ == '__main__':
    main()
