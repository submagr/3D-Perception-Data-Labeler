import subprocess
from collections import namedtuple
from pathlib import Path
from multiprocessing import Process, Queue
import json
import numpy as np
import trimesh
import pyrender
from matplotlib import pyplot as plt
from scipy.spatial.transform import Rotation as sciR
from pyrender import RenderFlags
import math
import pickle
from .bc_dataset import CameraData


def extract_masks(
    pose_json_path: Path,
    camera_data: CameraData,
    object_set_name: str,
    gt_meshes_dir: Path,
    plt_title: str = "",
    visualize=False,
):
    with open(pose_json_path, "r") as fp:
        updated_scene = json.load(fp)

    rgb, d, camera_depth_intr, camera_pose = (
        camera_data.rgb,
        camera_data.depth,
        camera_data.camera_k,
        camera_data.camera_extr,
    )

    scene = pyrender.Scene()
    fx = camera_depth_intr[0, 0]
    fy = camera_depth_intr[1, 1]
    cx = camera_depth_intr[0, 2]
    cy = camera_depth_intr[1, 2]
    cam = pyrender.camera.IntrinsicsCamera(fx, fy, cx, cy, znear=0.01, zfar=10)
    camera_pose[:, 1:3] = -camera_pose[:, 1:3]
    cam_node = pyrender.Node(camera=cam, matrix=camera_pose)
    scene.add_node(cam_node)

    light = pyrender.SpotLight(
        color=np.ones(3),
        intensity=3.0,
        innerConeAngle=np.pi / 16.0,
        outerConeAngle=np.pi / 6.0,
    )
    scene.add(light, pose=camera_pose)

    updated_objects = updated_scene["objects"]
    node_mask = dict()
    mask_id_to_class = dict()

    # Create gt_meshes_name to path mapping
    with open(gt_meshes_dir / "gt_meshes.json", "r") as fp:
        gt_meshes_json = json.load(fp)
    gt_meshes_name_to_path = dict() 
    for mesh_details in gt_meshes_json:
        gt_meshes_name_to_path[mesh_details["name"]] = gt_meshes_dir / mesh_details["path"]

    for obj_index, updated_obj in enumerate(updated_objects):
        if (
            object_set_name is not None
            and object_set_name not in updated_obj["present_in_object_set"]
        ):
            continue

        pos = updated_obj["position"]
        ori = updated_obj["orientation"]
        # mesh_name = Path(updated_obj["path"]).stem
        mesh_name = updated_obj["name"]
        if not mesh_name in gt_meshes_name_to_path:
            continue

        mesh_path = gt_meshes_name_to_path[mesh_name]

        T = np.identity(4)
        T[:3, :3] = sciR.from_quat(ori).as_matrix()
        T[:3, 3] = pos
        mesh = trimesh.load_mesh(mesh_path)
        mesh = pyrender.Mesh.from_trimesh(mesh)
        mesh_node = pyrender.Node(mesh=mesh, matrix=T)
        scene.add_node(mesh_node)
        mask_id = obj_index + 1
        node_mask[mesh_node] = mask_id
        mask_id_to_class[mask_id] = mesh_name

    r = pyrender.OffscreenRenderer(d.shape[1], d.shape[0])
    color_mask, depth = r.render(scene, RenderFlags.SEG, node_mask)
    mask = color_mask[:, :, 0]
    mask_values = list(node_mask.values())

    data = []
    mask_object_indices = []
    if visualize:
        nrows = 3
        ncols = math.ceil((len(mask_values) + 1) / nrows)
        fig, axs = plt.subplots(nrows, ncols, squeeze=False)
        axs[0, 0].imshow(rgb)
    for mask_ind, mask_value in enumerate(mask_values):
        mask_class = mask_id_to_class[mask_value]
        mask_array = mask == mask_value
        data.append({"class": mask_class, "mask_array": mask_array})
        mask_object_indices.append(mask_value - 1)
        if visualize:
            mask_ind += 1
            i = mask_ind // ncols
            j = mask_ind % ncols
            axs[i, j].imshow(rgb)
            axs[i, j].imshow(mask_array, alpha=0.5, cmap="jet")
            axs[i, j].set_title(mask_class)

    if visualize:
        plt.suptitle(plt_title)
        plt.show()
        plt.close()

    return data, mask_object_indices

    # List of dicts saying obj_name, mask_array.


def extract_masks_helper(args):
    json_path, view_pkl, object_set_name, gt_meshes_dir = args
    mask_save_path = view_pkl.parent / f"{view_pkl.stem}_label_mask.pkl"
    print("=======>FIXME<======= IGNORED MASK CACHING")
    # if mask_save_path.exists():
    #     print(f"Interpolated data already exists: {mask_save_path}")
    #     return

    with open(view_pkl, "rb") as fp:
        view_data = pickle.load(fp)
    MyCameraData = namedtuple(
        "MyCameraData", ["rgb", "depth", "camera_k", "camera_extr"]
    )
    my_camera_data = MyCameraData(
        view_data["rgb"],
        view_data["depth"],
        view_data["camera_intrinsics"],
        np.linalg.inv(view_data["tag_pose"]),
    )
    data, _ = extract_masks(
        json_path,
        my_camera_data,
        object_set_name,
        gt_meshes_dir,
        str(view_pkl),
        visualize=False,
    )
    with open(mask_save_path, "wb") as fp:
        pickle.dump(data, fp)

    print("Mask saved at path", mask_save_path)
    return mask_save_path, data, view_data["rgb"]

def get_mask_rgb_save_path(scene_dir):
    return scene_dir / "mask.png", scene_dir / "rgb.png"

def extract_mask_helper_run_in_seperate_process(args):
    json_path, view_pkl, _, gt_meshes_dir = args
    subprocess.run(
        [
            "python",
            "generate_single_label.py",
            json_path.absolute(),
            view_pkl.absolute(),
            gt_meshes_dir.absolute(),
        ],
        stdout=subprocess.PIPE,
    )
