"""Source-qualified East Asia CLI; datasets are supplied separately from Git."""
from pathlib import Path
import os
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import east_asia_sources
import east_asia_projection
import east_asia_query
import tw_nlsc_reference


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'lookup':
        del sys.argv[1]
        if '--data-root' not in sys.argv and os.environ.get('WORLD_LOCALITIES_ADDRESS_ROOT'):
            sys.argv.extend(['--data-root', os.environ['WORLD_LOCALITIES_ADDRESS_ROOT']])
        east_asia_query.main(); return
    if '--source-projection' in sys.argv:
        sys.argv.remove('--source-projection')
        if '--data-root' not in sys.argv and os.environ.get('WORLD_LOCALITIES_ADDRESS_ROOT'):
            sys.argv.extend(['--data-root', os.environ['WORLD_LOCALITIES_ADDRESS_ROOT']])
        east_asia_projection.main(); return
    if '--source=TW-NLSC' in sys.argv:
        sys.argv.remove('--source=TW-NLSC')
        tw_nlsc_reference.main(); return
    if '--source' in sys.argv:
        at = sys.argv.index('--source')
        if len(sys.argv) > at + 1 and sys.argv[at + 1] == 'TW-NLSC':
            del sys.argv[at:at + 2]
            if '--data-root' not in sys.argv:
                raise ValueError('NLSC requires --data-root pointing to the tw-nlsc directory')
            tw_nlsc_reference.main(); return
    if '--data-root' not in sys.argv and os.environ.get('WORLD_LOCALITIES_ADDRESS_ROOT'):
        sys.argv.extend(['--data-root', os.environ['WORLD_LOCALITIES_ADDRESS_ROOT']])
    east_asia_sources.main()


if __name__ == '__main__': main()
