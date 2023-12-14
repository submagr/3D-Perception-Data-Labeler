import "../css/main.scss";
import { GTObjListStore } from "./model/gt_obj_list_store.js";
import { ObjListStore } from "./model/obj_list_store.js";
import { PointCloudStore } from "./model/point_cloud_store.js";
import { LabelerMeshListStore } from "./model/labeler_mesh_list_store.js";
import { ObjAdderViewer } from "./view/obj_adder_viewer.js";
import { ObjListViewer } from "./view/obj_list_viewer.js";
import { ThreeLabelerViewer } from "./view/three_labeler_viewer.js";
import { LabelerMeshListViewer } from "./view/labeler_mesh_list_viewer.js";
import { PointCloudViewer } from "./view/point_cloud_viewer.js";
import { ObjAdderController } from "./controller/obj_adder_controller.js";
import { ObjListController } from "./controller/obj_list_controller.js";
import { LabelerMeshListController } from "./controller/labeler_mesh_list_controller.js";
import { PointCloudController } from "./controller/point_cloud_controller.js";
import { animate_three_scenes } from "./view/three_viewer_base.js";
import { get_current_url_params } from "./controller/utils.js";

const SCENE_ROOT_PATH = "static/scene";
const GT_MESHES_PATH = "data/gt_meshes";
const GT_MESHES_JSON_PATH = `${GT_MESHES_PATH}/gt_meshes.json`;
const SCENE_JSON_PATH = `${SCENE_ROOT_PATH}/scene.json`;
const SERVER_URL = "http://lambda03.saicny.com:5000";

function main() {
    const url_params = get_current_url_params();
    if (!url_params.has("scene")) {
        alert("Please specify scene id in url like localhost:5000/?scene=0");
        throw new Error("scene is not specified in URL");
    }
    const scene_ind = url_params.get("scene");

    // setup object-selector
    var gt_obj_list_store = new GTObjListStore(GT_MESHES_JSON_PATH);
    var obj_adder_viewer = new ObjAdderViewer("obj-selector", "obj-add");
    var obj_adder_controller = new ObjAdderController(gt_obj_list_store, obj_adder_viewer);

    // setup object-list
    var obj_list_store = new ObjListStore(SERVER_URL, scene_ind);
    var obj_list_viewer = new ObjListViewer("obj-list-table", "obj-list-radio");
    var obj_list_controller = new ObjListController(obj_list_store, gt_obj_list_store, obj_list_viewer);

    // hook up the obj-adder add button with obj-list
    obj_adder_controller.register_obj_add_callback(
        obj_list_controller.add_to_obj_info_list_callback.bind(obj_list_controller)
    );

    // now let's create the labeler viewer.
    var three_labeler_viewer = new ThreeLabelerViewer("three_main_canvas");
    var three_scenes = [];
    three_scenes.push(three_labeler_viewer);
    obj_list_controller.register_obj_selection_change_callback(
        three_labeler_viewer.active_obj_change_handler.bind(three_labeler_viewer)
    );
    // point-cloud mvc
    var point_cloud_store = new PointCloudStore(scene_ind);
    point_cloud_store.load_pc();
    var point_cloud_viewer = new PointCloudViewer("set-pcl-visiblity");
    var point_cloud_controller = new PointCloudController(point_cloud_store, point_cloud_viewer);
    point_cloud_controller.register_add_pc_callback(
        three_labeler_viewer.add_pc_handler.bind(three_labeler_viewer)
    );

    // Objs In Labeler mvc
    var labeler_mesh_list_store = new LabelerMeshListStore(SERVER_URL, scene_ind);
    var labeler_mesh_list_viewer = new LabelerMeshListViewer(
        "save-button", "save-and-render-button");
    var labeler_mesh_list_controller = new LabelerMeshListController(
        labeler_mesh_list_store, gt_obj_list_store, labeler_mesh_list_viewer, GT_MESHES_PATH);
    obj_list_store.register_obj_info_list_add_callback(
        labeler_mesh_list_controller.obj_info_list_add_handler.bind(labeler_mesh_list_controller)
    );
    labeler_mesh_list_controller.register_add_mesh_callback(
        three_labeler_viewer.add_mesh_handler.bind(three_labeler_viewer)
    );
    obj_list_controller.register_get_icp_button_click_callback(
        labeler_mesh_list_controller.get_icp_button_click_handler.bind(labeler_mesh_list_controller)
    );
    obj_list_controller.register_toggle_vis_button_click_callback(
        labeler_mesh_list_controller.toggle_vis_button_click_handler.bind(labeler_mesh_list_controller)
    );

    animate_three_scenes(three_scenes);
}
main();