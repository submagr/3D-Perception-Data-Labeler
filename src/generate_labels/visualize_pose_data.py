# sample script to visualize the pose data
from collections import namedtuple
from pathlib import Path
import json
import re
import numpy as np
import trimesh
import pyrender
from scipy.spatial.transform import Rotation as sciR
import pickle
import open3d as o3d
from label_data import gt_mesh_paths


def main():
    root = Path("/labdata/shubham/Dev/ol22_perception/data/seg_real_new/")
    get_child_dirs = lambda path: [x for x in path.iterdir() if x.is_dir()]
    for scene_dir in get_child_dirs(root):
        json_path = scene_dir / "labels_object_set_0__lighting_0__view_3.pkl.json"
        if not json_path.exists():
            print("Scene not labelled: ", json_path, ". Ignoring.")
            continue
        # Parallel to every view, create a mask.pkl file saying a list of dict
        # {obj_name, mask array}. Cool.

        for object_set_dir in get_child_dirs(scene_dir):
            for lighting_dir in get_child_dirs(object_set_dir):
                view_pkls = [
                    x
                    for x in lighting_dir.iterdir()
                    if re.match("view_\d+\.pkl", x.name)
                ]
                for view_pkl in view_pkls:
                    print(f"============ Showing {view_pkl} ============")
                    with open(view_pkl, "rb") as fp:
                        view_data = pickle.load(fp)
                    rgb, d, camera_depth_intr, camera_pose = (
                        view_data["rgb"],
                        view_data["depth"],
                        view_data["camera_intrinsics"],
                        np.linalg.inv(view_data["tag_pose"]),
                    )
                    camera_T_world = np.linalg.inv(
                        camera_pose
                    )  # camera_pose is world_T_camera

                    # Convert RGB-D camera_k to point-cloud
                    o3d_rgb = o3d.geometry.Image(rgb)
                    o3d_depth = o3d.geometry.Image(d)
                    o3d_rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
                        o3d_rgb, o3d_depth, convert_rgb_to_intensity=False
                    )
                    o3d_camera_k = o3d.camera.PinholeCameraIntrinsic(
                        rgb.shape[0],
                        rgb.shape[1],
                        camera_depth_intr[0, 0],
                        camera_depth_intr[1, 1],
                        camera_depth_intr[0, 2],
                        camera_depth_intr[1, 2],
                    )
                    o3d_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
                        o3d_rgbd, o3d_camera_k
                    )

                    # Get pose of objects in the camera frame.
                    o3d_meshes = []
                    with open(json_path, "r") as fp:
                        updated_scene = json.load(fp)
                    updated_objects = updated_scene["objects"]
                    for obj_index, updated_obj in enumerate(updated_objects):
                        mesh_name = Path(updated_obj["path"]).stem
                        mesh_path = gt_mesh_paths[mesh_name]
                        o3d_mesh = o3d.io.read_triangle_mesh(str(mesh_path))
                        # Transform mesh to the camera frame
                        pos = updated_obj["position"]
                        ori = updated_obj["orientation"]
                        world_T_obj = np.identity(4)
                        world_T_obj[:3, :3] = sciR.from_quat(ori).as_matrix()
                        world_T_obj[:3, 3] = pos
                        camera_T_obj = camera_T_world @ world_T_obj
                        o3d_mesh = o3d_mesh.transform(camera_T_obj)
                        o3d_meshes.append(o3d_mesh)
                    o3d.visualization.draw([o3d_pcd] + o3d_meshes)


if __name__ == "__main__":
    main()
