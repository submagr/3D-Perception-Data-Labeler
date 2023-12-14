"""Contains utilities to read project-wide constant paths."""
import os
from pathlib import Path


def get_static_dir_path() -> Path:
    return Path(os.environ["STATIC_DIR"])


def get_data_dir_path() -> Path:
    return Path(os.environ["DATA_DIR"])


def get_gt_meshes_path() -> Path:
    return get_data_dir_path() / "gt_meshes"


def get_logs_dir() -> Path:
    return Path(os.environ["LOGS_DIR"])

