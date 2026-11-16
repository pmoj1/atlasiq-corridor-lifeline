"""Local collection coordinator. Fixed config, one worker, explicit refresh only."""
from datetime import datetime, timezone
from pathlib import Path
import threading
import copy
from .__main__ import load_config, run_once
from .history import recent


class Workspace:
    def __init__(self, config, out):
        self.config = Path(config).resolve()
        self.out = Path(out).resolve()
        self.lock = threading.Lock()
        self.state = {'running': False, 'completed_at': None, 'error': None}

    def status(self):
        with self.lock:
            return dict(self.state)

    def start(self):
        with self.lock:
            if self.state['running']:
                return False
            self.state = {'running': True, 'completed_at': None, 'error': None}
        threading.Thread(target=self._collect, daemon=True).start()
        return True

    def _collect(self):
        error = None
        try:
            config = load_config(self.config)
            run_once(config, self.config.parent, self.out, datetime.now(timezone.utc))
        except Exception as exc:
            error = str(exc)
        finally:
            with self.lock:
                self.state = {'running': False, 'completed_at': datetime.now(timezone.utc).isoformat(), 'error': error}

    def history(self):
        return recent(self.out / 'history.sqlite3')

    def context_status(self):
        with self.lock:
            state = copy.deepcopy(getattr(self, '_context_state', {'running': False, 'error': None, 'data': None}))
        for source in (state.get('data') or {}).get('sources', []):
            if source.get('status') in ('ok', 'stale'):
                try:
                    stamp = datetime.fromisoformat(source['generated_at'].replace('Z', '+00:00'))
                    age = (datetime.now(timezone.utc) - stamp).total_seconds()
                    source['status'] = 'unknown' if age < -300 else ('stale' if age > source.get('max_age_minutes', 30) * 60 else ('partial' if source.get('rejected_count') or source.get('partial') else 'ok'))
                except (KeyError, TypeError, ValueError):
                    source['status'] = 'unknown'
        return state

    def start_context(self):
        with self.lock:
            old = getattr(self, '_context_state', {'data': None})
            if old.get('running'):
                return False
            self._context_state = {'running': True, 'error': None, 'data': old.get('data')}
        threading.Thread(target=self._collect_context, daemon=True).start()
        return True

    def _collect_context(self):
        try:
            from .context import fetch_all_context
            data = fetch_all_context()
            with self.lock:
                self._context_state = {'running': False, 'error': None, 'data': data}
        except Exception:
            with self.lock:
                self._context_state.update(running=False, error='Context collection failed. Any displayed previous events are not refreshed.')
