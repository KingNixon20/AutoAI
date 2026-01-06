from pathlib import Path
import yaml
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def load_config_cached() -> dict:
    p = _config_path()
    try:
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except Exception:
        return {}
    return {}


def _config_path() -> Path:
    return Path.home() / '.config' / 'autoai' / 'config.yaml'


def load_config() -> dict:
    # non-cached loader
    return load_config_cached()


def save_config(data: dict):
    p = _config_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f)
        # invalidate cache
        load_config_cached.cache_clear()
    except Exception:
        pass


def set_projects_dir(path: str):
    cfg = load_config()
    cfg['projects_dir'] = path
    save_config(cfg)


def get_projects_dir() -> Path:
    cfg = load_config()
    p = cfg.get('projects_dir')
    if p:
        return Path(os.path.expanduser(p))
    return Path.cwd() / 'projects'
