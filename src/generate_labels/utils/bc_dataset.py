"""
BenchmarkDataset class to access dataset
"""
from pathlib import Path
from typing import Tuple, Union
import numpy as np


class CameraData:
    """Contains camera data"""

    def __init__(self, data_path: Path, cam_prefix: str) -> None:
        def load_np_if_exists(path: Path) -> Union[None, np.ndarray]:
            arr = None
            if path.exists():
                arr = np.load(path)
            return arr

        self.data_path = data_path
        self.cam_prefix = cam_prefix
        self.depth = load_np_if_exists(self.data_path / f"{cam_prefix}_depth.npy")
        self.rgb = load_np_if_exists(self.data_path / f"{cam_prefix}_rgb.npy")
        self.mask = load_np_if_exists(self.data_path / f"{cam_prefix}_mask.npy")
        self.camera_k = load_np_if_exists(self.data_path / f"{cam_prefix}_camera_k.npy")
        self.camera_extr = load_np_if_exists(
            self.data_path / f"{cam_prefix}_camera_extr.npy"
        )
        self.camera_serial_num = load_np_if_exists(
            self.data_path / f"{cam_prefix}_camera_serial_num.npy"
        )


class BenchmarkDataset:
    def __init__(self, dataset_root: Path) -> None:
        self.dataset_root = dataset_root
        self.datapoint_paths = []
        for datapoint_path in bc_dataset_path_iterator(self.dataset_root):
            self.datapoint_paths.append(datapoint_path)

    def __len__(self) -> int:
        return len(self.datapoint_paths)

    def __getitem__(self, index: int) -> Tuple[CameraData, CameraData]:
        data_path = self.datapoint_paths[index]
        return {
            "side": CameraData(data_path, "side"),
            "top": CameraData(data_path, "top_down")
        }
    

def bc_dataset_path_iterator(dataset_root: Path):
    for datapoint_path in dataset_root.iterdir():
        if datapoint_path.name.isdigit():
            yield datapoint_path
