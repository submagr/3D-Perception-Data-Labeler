# Quick test file to save pointcloud
from pathlib import Path
import json
import pickle
import numpy as np
import open3d as o3d
from scipy.spatial.transform import Rotation as sciR
from shutil import copy
from matplotlib import pyplot as plt
from utils.pointcloud import PointCloud


RBS_MODEL_ROOT = Path("/home/submagr/Dev/RBS/")
gt_mesh_paths = {
    "bowl": RBS_MODEL_ROOT
    / "environment/model/benchmark_obj/bowl/textured_transformed.obj",
    "plate": RBS_MODEL_ROOT
    / "environment/model/benchmark_obj/plate/textured_simple.obj",
    "mug": RBS_MODEL_ROOT
    / "environment/model/benchmark_obj/mug/textured_transformed.obj",
    "spoon": RBS_MODEL_ROOT
    / "environment/model/benchmark_obj/spoon/textured_transformed.obj",
    "fork": RBS_MODEL_ROOT
    / "environment/model/benchmark_obj/fork/textured_transformed.obj",
    "knife": RBS_MODEL_ROOT
    / "environment/model/benchmark_obj/knife/textured_transformed.obj",
}


def main():
    DATA_LABEL_SCENE_PATH = Path("visualizer/client/dist/scenes/json_scene/")

    dataset_root = Path("/labdata/shubham/Dev/ol22_perception/data/seg_real_new/")
    existing_scene_paths = [
        int(scene_path.stem.split("_")[-1])
        for scene_path in dataset_root.glob("scene_*")
        if scene_path.is_dir()
    ]

    # Ask the user a scene to label
    for scene_counter in existing_scene_paths:
        scene_dir = dataset_root / f"scene_{scene_counter}"
        scene_counter += 1
        print(scene_dir)
        if not scene_dir.is_dir():
            continue
        
        path_view_to_label = "object_set_0/lighting_0/view_3.pkl"
        labels_save_path = (
            scene_dir / f"labels_{path_view_to_label.replace('/', '__')}.json"
        )

        print("Saving labels to:", labels_save_path)
        if labels_save_path.exists():
            print("Already labeled, skipping")
            continue

        view_path = scene_dir / path_view_to_label
        if not view_path.exists():
            print(f"{view_path} does not exist")
            continue

        with open(view_path, "rb") as fp:
            view_data = pickle.load(fp)
        rgb, d, camera_depth_intr, camera_pose = (
            view_data["rgb"],
            view_data["depth"],
            view_data["camera_intrinsics"],
            np.linalg.inv(view_data["tag_pose"]),
        )
        d = d.astype(float) / 1000

        # Dump scene information
        scene_info = {
            "objects": [],
            "gt_objects": [],
        }
        plt.imsave("rgb.png", rgb)
        print("Please check the image rgb.png and answer the questions:")
        for mesh_name, mesh_path in gt_mesh_paths.items():
            print(f"Number of {mesh_name} instances?: ")
            num_meshes = int(input())
            for _ in range(num_meshes):
                scene_info["gt_objects"].append(
                    {
                        "path": f"{mesh_name}.obj",
                        "orientation": [0, 0, 0, 1],
                        "position": [0, 0, 0],
                    }
                )
        with open(DATA_LABEL_SCENE_PATH / f"scene.json", "w") as fp:
            json.dump(scene_info, fp)

        for mesh_name, mesh_path in gt_mesh_paths.items():
            copy(mesh_path, DATA_LABEL_SCENE_PATH / f"{mesh_name}.obj")

        # Dump pointcloud
        pcl = PointCloud(rgb, d, camera_depth_intr)
        pcl.make_pointcloud()
        o3d_pc_full = pcl.o3d_pc
        o3d_pc_full = o3d_pc_full.transform(camera_pose)
        # Add additional 180 rotation around x axis from tag frame
        extra_transformation = np.eye(4)
        extra_transformation[:3, :3] = sciR.from_euler(
            "xyz", [180, 0, 0], degrees=True
        ).as_matrix()
        o3d_pc_full = o3d_pc_full.transform(extra_transformation)
        # o3d.visualization.draw([o3d_pc_full])

        def dump_point_cloud(pcl_path):
            xyz = np.array(o3d_pc_full.points)
            rgb = np.array(o3d_pc_full.colors)
            o3d_pc = o3d.geometry.PointCloud()
            o3d_pc.points = o3d.utility.Vector3dVector(xyz)
            o3d_pc.colors = o3d.utility.Vector3dVector(rgb)
            o3d.io.write_point_cloud(str(pcl_path), o3d_pc, write_ascii=True)
            return o3d_pc

        dump_point_cloud(DATA_LABEL_SCENE_PATH / f"scene_OBJECTS_pcl.ply")

        print("Press enter when the labeled scene from the user is ready")
        input()
        update_scene_path = Path("visualizer/server/updated_scene.json")
        with open(update_scene_path, "r") as fp:
            updated_scene = json.load(fp)
        new_updated_scene = {"objects": []}
        for obj in updated_scene["objects"]:
            mesh_path, pos, ori = obj["path"], obj["position"], obj["orientation"]
            # Just apply inverse transformation of the extra transformation
            T = np.eye(4)
            T[:3, :3] = sciR.from_quat(ori).as_matrix()
            T[:3, 3] = pos
            T = np.linalg.inv(extra_transformation) @ T
            new_updated_scene["objects"].append(
                {
                    "path": str(mesh_path),
                    "position": T[:3, 3].tolist(),
                    "orientation": sciR.from_matrix(T[:3, :3]).as_quat().tolist(),
                }
            )
        with open(labels_save_path, "w") as fp:
            json.dump(new_updated_scene, fp)


if __name__ == "__main__":
    main()
