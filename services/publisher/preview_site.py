"""Faithful preview of a review package: builds the real site from a snapshot where the package's
drafts count as approved. The result is a static folder; nothing is deployed and nothing is persisted
in the CMS. One folder per submission; the review server serves the active one at its own origin
because the site uses absolute paths and cannot live under a URL prefix."""
import json
import shutil
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cms'))
from core import Error, now
from run_release import ROOT, build, digest, staging_directory


class PreviewBuilder:
    def __init__(self, output_dir, root=ROOT, builder=build, synchronous=False):
        self.output, self.root, self.builder, self.synchronous = Path(output_dir), root, builder, synchronous
        self.output.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.active = None

    def _path(self, submission_id):
        if not submission_id.replace('-', '').isalnum():
            raise Error(422, 'invalid_id', 'Identificador inválido.')
        return self.output / submission_id

    def _status_file(self, submission_id):
        return self.output / (submission_id + '.json')

    def state(self, submission_id):
        path = self._status_file(submission_id)
        if not path.is_file():
            return {'state': 'none'}
        value = json.loads(path.read_text(encoding='utf-8'))
        value['active'] = self.active == submission_id
        return value

    def _write(self, submission_id, **value):
        self._status_file(submission_id).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def start(self, make_snapshot, submission_id):
        with self.lock:
            current = self.state(submission_id)
            if current['state'] == 'building':
                return current
            self._write(submission_id, state='building', startedAt=now())
        if self.synchronous:
            self._run(make_snapshot, submission_id)
        else:
            threading.Thread(target=self._run, args=(make_snapshot, submission_id), daemon=True).start()
        return self.state(submission_id)

    def _run(self, make_snapshot, submission_id):
        try:
            snapshot = make_snapshot()  # raises Error when the package is not publishable
            marker = {'releaseId': snapshot['releaseId'], 'snapshotSha256': digest(snapshot), 'containsDemo': False}
            with staging_directory() as temporary:
                artifact = self.builder(self.root, temporary / 'web', snapshot, marker)
                target = self._path(submission_id)
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(artifact, target)
            self.active = submission_id
            self._write(submission_id, state='ready', builtAt=now(), round=snapshot['releaseId'].rsplit('-r', 1)[-1])
        except Error as error:
            self._write(submission_id, state='failed', error=str(error), code=error.code, finishedAt=now())
        except Exception as error:  # build output may contain paths; keep only the exception type
            self._write(submission_id, state='failed', error='A prévia não pôde ser gerada (' + type(error).__name__ + ').', finishedAt=now())

    def activate(self, submission_id):
        if self.state(submission_id)['state'] != 'ready' or not self._path(submission_id).is_dir():
            raise Error(409, 'not_ready', 'A prévia ainda não foi gerada.')
        self.active = submission_id

    def active_directory(self):
        return self._path(self.active) if self.active else None
