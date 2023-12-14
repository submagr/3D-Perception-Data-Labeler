from importlib.resources import path
from pathlib import Path
from copy import deepcopy
import pickle
import re
import numpy as np
import json
import open3d as o3d
from scipy.spatial.transform import Rotation as sciR
from matplotlib import pyplot as plt

from .render_utils import (
    extract_mask_helper_run_in_seperate_process,
    get_mask_rgb_save_path,
)
from .pointcloud import PointCloud


def dump_point_cloud(pcl_path, o3d_pc_full):
    xyz = np.array(o3d_pc_full.points)
    rgb = np.array(o3d_pc_full.colors)
    o3d_pc = o3d.geometry.PointCloud()
    o3d_pc.points = o3d.utility.Vector3dVector(xyz)
    o3d_pc.colors = o3d.utility.Vector3dVector(rgb)
    o3d.io.write_point_cloud(str(pcl_path), o3d_pc, write_ascii=True)
    return o3d_pc


def get_pcl_extra_transformation():
    # Add additional 180 rotation around x axis from tag frame
    extra_transformation = np.eye(4)
    extra_transformation[:3, :3] = sciR.from_euler(
        "xyz", [180, 0, 0], degrees=True
    ).as_matrix()
    return extra_transformation


def get_path_view_to_label():
    return "object_set_0/lighting_0/view_3.pkl"


def get_all_view_paths(view_dir):
    view_pkls = [x for x in view_dir.iterdir() if re.match("view_\d+\.pkl", x.name)]
    return view_pkls


def get_scene_pcl_path(scene_dir, use_all_views: bool = True):
    scene_pcl_path = scene_dir / "scene_pcl.ply"
    if scene_pcl_path.exists():
        return True, scene_pcl_path
    print("Scene pcl not found, generating...")

    path_view_to_label = scene_dir / get_path_view_to_label()
    if use_all_views:
        view_paths = get_all_view_paths(path_view_to_label.parent)
    else:
        view_paths = [path_view_to_label]

    pcls = []
    for view_path in view_paths:
        if not view_path.exists():
            print(f"{view_path} does not exist")
            continue

        with open(view_path, "rb") as fp:
            view_data = pickle.load(fp)

        rgb, depth, camera_k, robot_T_camera = (
            view_data["rgb"],
            view_data["depth"],
            view_data["camera_intrinsics"],
            np.linalg.inv(view_data["tag_pose"]),
        )
        o3d_rgb = o3d.geometry.Image(rgb)
        o3d_depth = o3d.geometry.Image(depth)
        o3d_rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d_rgb, o3d_depth, depth_scale=1000, convert_rgb_to_intensity=False
        )
        o3d_pcl = o3d.geometry.PointCloud.create_from_rgbd_image(
            o3d_rgbd,
            o3d.camera.PinholeCameraIntrinsic(
                width=depth.shape[1],
                height=depth.shape[0],
                fx=camera_k[0, 0],
                fy=camera_k[1, 1],
                cx=camera_k[0, 2],
                cy=camera_k[1,2],
            )
        )
        o3d_pcl = o3d_pcl.transform(robot_T_camera)
        _, in_ind = o3d_pcl.remove_statistical_outlier(
            nb_neighbors=50, std_ratio=0.5
        )
        o3d_pcl = o3d_pcl.select_by_index(in_ind)
        extra_transformation = get_pcl_extra_transformation()
        o3d_pcl = o3d_pcl.transform(extra_transformation)
        pcls.append(o3d_pcl)

    if len(pcls) == 0:
        return False, None

    pcl_combined = o3d.geometry.PointCloud()
    for point_id in range(len(pcls)):
        pcl_combined += pcls[point_id]
    # o3d.visualization.draw([pcl_combined])
    dump_point_cloud(scene_pcl_path, pcl_combined)
    return True, scene_pcl_path


def save_scene_labels(scene_dir, updated_scene):
    new_updated_scene = {"objects": []}
    extra_transformation = get_pcl_extra_transformation()
    path_view_to_label = get_path_view_to_label()
    labels_save_path = (
        scene_dir / f"labels_{path_view_to_label.replace('/', '__')}.json"
    )
    for obj in updated_scene["objects"]:
        mesh_name, pos, ori = obj["name"], obj["position"], obj["orientation"]
        # Just apply inverse transformation of the extra transformation
        T = np.eye(4)
        T[:3, :3] = sciR.from_quat(ori).as_matrix()
        T[:3, 3] = pos
        T = np.linalg.inv(extra_transformation) @ T
        new_updated_scene["objects"].append(
            {
                "name": str(mesh_name),
                "position": T[:3, 3].tolist(),
                "orientation": sciR.from_matrix(T[:3, :3]).as_quat().tolist(),
            }
        )
    with open(labels_save_path, "w") as fp:
        json.dump(new_updated_scene, fp)
    return True


def get_scene_json_path(scene_dir):
    path_view_to_label = get_path_view_to_label()
    labels_save_path = (
        scene_dir / f"labels_{path_view_to_label.replace('/', '__')}.json"
    )
    if not labels_save_path.exists():
        return False, None
    with open(labels_save_path, "r") as fp:
        scene_data = json.load(fp)
        # Apply extra transformation
        extra_transformation = get_pcl_extra_transformation()
        for i, obj_data in enumerate(scene_data["objects"]):
            T = np.eye(4)
            T[:3, :3] = sciR.from_quat(obj_data["orientation"]).as_matrix()
            T[:3, 3] = obj_data["position"]
            T = extra_transformation @ T
            obj_data["position"] = (T[:3, 3] / T[3, 3]).tolist()
            obj_data["orientation"] = sciR.from_matrix(T[:3, :3]).as_quat().tolist()
            scene_data["objects"][i] = obj_data
    return True, scene_data


def get_icp_poses(scene_dir, gt_meshes_dir, icp_data):
    # Get the path to the scene pcl
    success, pcl_path = get_scene_pcl_path(scene_dir)
    if not success:
        print("scene pointcloud not found")
        return success, None
    # Load the point-cloud in open3d
    o3d_pcl = o3d.io.read_point_cloud(str(pcl_path))
    # Load the object mesh
    mesh_name = icp_data["object"]["name"]
    mesh_path = gt_meshes_dir / f"{mesh_name}.obj"
    o3d_mesh = o3d.io.read_triangle_mesh(str(mesh_path))
    o3d_mesh_pcd = o3d_mesh.sample_points_uniformly(number_of_points=5000)
    # - apply mesh transformations
    T = np.eye(4)
    T[:3, 3] = icp_data["object"]["position"]
    T[:3, :3] = sciR.from_quat(icp_data["object"]["orientation"]).as_matrix()
    o3d_mesh_pcd = o3d_mesh_pcd.transform(T)
    # - run ICP
    threshold = 5
    evaluation = o3d.pipelines.registration.evaluate_registration(
        o3d_mesh_pcd, o3d_pcl, threshold, np.eye(4),
    )
    evaluation = o3d.pipelines.registration.registration_icp(
        o3d_mesh_pcd,
        o3d_pcl,
        threshold,
        np.eye(4),
        o3d.pipelines.registration.TransformationEstimationPointToPoint(),
        # o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=100),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=2000),
    )

    # print("ICP evaluation:", evaluation.transformation)
    # o3d_mesh_icp_pcd = deepcopy(o3d_mesh_pcd).transform(evaluation.transformation)
    # o3d_mesh = o3d_mesh.transform(T)
    # o3d_mesh_icped = deepcopy(o3d_mesh).transform(evaluation.transformation)
    # o3d.visualization.draw([o3d_pcl, o3d_mesh_pcd, o3d_mesh_icp_pcd, o3d_mesh, o3d_mesh_icped])

    new_world_pose = T @ evaluation.transformation
    new_pose_data = {
        "name": mesh_name,
        "position": (new_world_pose[:3, 3] / new_world_pose[3, 3]).tolist(),
        "orientation": sciR.from_matrix(new_world_pose[:3, :3]).as_quat().tolist(),
    }
    return True, new_pose_data


def render_scene(scene_dir, gt_meshes_dir: Path):
    # How are we supposed to render the scene?
    # Let's get the rendering parameters
    json_path = scene_dir / "labels_object_set_0__lighting_0__view_3.pkl.json"
    if not json_path.exists():
        print("Corrected json is not present: ", json_path)
        return False, None
    object_set_dir = scene_dir / "object_set_0"
    view_pkl = object_set_dir / "lighting_0/view_0.pkl"
    extract_mask_helper_run_in_seperate_process(
        (json_path, view_pkl, None, gt_meshes_dir)
    )
    return True, get_mask_rgb_save_path(scene_dir)[0]
