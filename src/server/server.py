from pathlib import Path
import os
import json
from flask import Flask, request, send_file
from flask_cors import CORS
import constant_paths
from generate_labels.utils.scene_utils import (
    get_scene_pcl_path,
    save_scene_labels,
    get_scene_json_path,
    get_icp_poses,
    render_scene,
    get_mask_rgb_save_path,
)


STATIC_DIR = constant_paths.get_static_dir_path()
DATA_DIR = constant_paths.get_data_dir_path()
GT_MESHES_DIR = constant_paths.get_gt_meshes_path()
app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="")
cors = CORS(app)


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/save_scene", methods=["POST"])
def save_scene():
    scene_ind = request.args.get("scene")
    scene_dir = DATA_DIR / f"scene_{scene_ind}"
    success = save_scene_labels(scene_dir, request.json)
    if success:
        return "Scene saved successfully!"
    else:
        return "Scene could not be saved", 400


@app.route("/save_and_render_scene", methods=["POST"])
def save_and_render_scene():
    scene_ind = request.args.get("scene")
    scene_dir = DATA_DIR / f"scene_{scene_ind}"
    success = save_scene_labels(scene_dir, request.json)
    if success:
        success, mask_save_path = render_scene(scene_dir, GT_MESHES_DIR)
        if success:
            return send_file(mask_save_path, mimetype="image/png")
        else:
            return "Scene saved but mask couldn't be rendered!", 400
    else:
        return "Scene could not be saved", 400


@app.route("/data/gt_meshes/<string:filename>")
def get_gt_mesh(filename):
    return app.send_static_file(f"{GT_MESHES_DIR.relative_to(STATIC_DIR)}/{filename}")


@app.route("/scene/<string:scene_index>/mask.png")
def get_scene_mask(scene_index):
    scene_path = DATA_DIR / f"scene_{scene_index}"
    mask_path = get_mask_rgb_save_path(scene_path)[0]
    if not mask_path.exists():
        return "mask not found", 404
    else:
        return app.send_static_file(
            f"{scene_path.relative_to(STATIC_DIR)}/{mask_path.name}"
        )


@app.route("/scene/<string:scene_index>/rgb.png")
def get_scene_rgb(scene_index):
    scene_path = DATA_DIR / f"scene_{scene_index}"
    rgb_path = get_mask_rgb_save_path(scene_path)[1]
    if not rgb_path.exists():
        return "rgb not found", 404
    else:
        return app.send_static_file(f"{scene_path.relative_to(STATIC_DIR)}/rgb.png")


@app.route("/scene/<string:scene_index>/pcl/scene_pcl.ply")
def get_scene_pcl(scene_index):
    scene_path = DATA_DIR / f"scene_{scene_index}"
    found, pcl_path = get_scene_pcl_path(scene_path)
    if not found:
        return "Scene not found", 404
    else:
        return app.send_static_file(pcl_path.relative_to(STATIC_DIR))


@app.route("/get_scene_labels")
def get_scene_labels():
    scene_ind = request.args.get("scene")
    scene_path = DATA_DIR / f"scene_{scene_ind}"
    found, scene_json_data = get_scene_json_path(scene_path)
    if not found:
        return f"Scene-{scene_ind} labels not found", 404
    else:
        response = app.response_class(
            response=json.dumps(scene_json_data),
            status=200,
            mimetype="application/json",
        )
        return response


@app.route("/get_icp", methods=["POST"])
def get_icp():
    icp_data = request.json
    scene_dir = DATA_DIR / f"scene_{icp_data['scene']}"
    success, new_pose_data = get_icp_poses(scene_dir, GT_MESHES_DIR, icp_data)
    if success:
        response = app.response_class(
            response=json.dumps(new_pose_data), status=200, mimetype="application/json",
        )
        return response
    else:
        return "Couldn't do ICP", 400
