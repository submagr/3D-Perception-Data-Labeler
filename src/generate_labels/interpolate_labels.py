import os
from pathlib import Path
import re
from multiprocessing import Pool
from tqdm import tqdm
import constant_paths
from utils.render_utils import extract_masks_helper


def main():
    gt_meshes_dir = constant_paths.get_gt_meshes_path()
    data_root = constant_paths.get_data_dir_path()
    get_child_dirs = lambda path: [x for x in path.iterdir() if x.is_dir()]

    with Pool(12) as my_pool:
        func_args = []
        for scene_dir in get_child_dirs(data_root):
            if not scene_dir.is_dir() or not scene_dir.name.startswith("scene_"):
                continue

            json_path = (
                scene_dir
                / "labels_object_set_0__lighting_0__view_3_object_set_info.pkl.json"
            )
            if not json_path.exists():
                print("Corrected json is not present: ", json_path, ". Ignoring.")
                continue
            for object_set_dir in get_child_dirs(scene_dir):
                for lighting_dir in get_child_dirs(object_set_dir):
                    view_pkls = [
                        x
                        for x in lighting_dir.iterdir()
                        if re.match("view_\d+\.pkl", x.name)
                    ]
                    for view_pkl in view_pkls:
                        func_args.append(
                            (json_path, view_pkl, object_set_dir.name, gt_meshes_dir)
                        )
        for _ in tqdm(
            my_pool.imap(extract_masks_helper, func_args), total=len(func_args)
        ):
            pass


if __name__ == "__main__":
    main()
