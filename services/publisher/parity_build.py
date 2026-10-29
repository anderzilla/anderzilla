"""Build the whole site from a CMS database (no Azure, no deploy) into a new local directory.
Used by step 4a to prove that the database reproduces what is live; refuses to overwrite its output."""
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from core import CMS
from run_release import ROOT, build, digest, staging_directory
from storage import SQLiteStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='new directory for the exported site')
    parser.add_argument('--release-id', required=True, help='release marker to stamp, e.g. the one of the live corpus')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists.')
    cms = CMS(SQLiteStore(args.database))
    with cms.store.transaction() as db:
        snapshot = cms.snapshot(db)
    snapshot['releaseId'] = args.release_id
    marker = {'releaseId': args.release_id, 'snapshotSha256': digest(snapshot), 'containsDemo': False}
    with staging_directory() as stage:
        artifact = build(ROOT, stage / 'web', snapshot, marker, preview=False)
        shutil.copytree(artifact, args.output)
    print(json.dumps({'output': str(args.output), 'marker': marker}, indent=2))


if __name__ == '__main__':
    main()
