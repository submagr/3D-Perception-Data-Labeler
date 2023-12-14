/* Controller for object meshes inside the main labeler*/

class LabelerMeshListController {
    constructor(labeler_mesh_list_store, gt_obj_list_store, labeler_mesh_list_viewer, gt_mesh_root_path) {
        this.labeler_mesh_list_store = labeler_mesh_list_store;
        this.gt_obj_list_store = gt_obj_list_store;
        this.labeler_mesh_list_viewer = labeler_mesh_list_viewer;
        this.gt_mesh_root_path = gt_mesh_root_path;
        this.add_mesh_callback_list = [];
        this.labeler_mesh_list_store.register_add_mesh_callback(
            this.add_mesh_handler.bind(this)
        );
        // save-button
        this.save_button_click_callback_list = [];
        this.labeler_mesh_list_viewer.register_save_button_click_callback(
            this.save_button_click_handler.bind(this)
        );
        this.register_save_button_click_callback(
            this.labeler_mesh_list_store.save_button_click_handler.bind(this.labeler_mesh_list_store)
        );
        // save_and_render button
        this.save_and_render_button_click_callback_list = [];
        this.labeler_mesh_list_viewer.register_save_and_render_button_click_callback(
            this.save_and_render_button_click_handler.bind(this)
        );
        this.register_save_and_render_button_click_callback(
            this.labeler_mesh_list_store.save_and_render_button_click_handler.bind(this.labeler_mesh_list_store)
        );
    }

    obj_info_list_add_handler(obj_info, obj_index) {
        /* Handle when an object is added to obj-info list */
        var [gt_mesh_ind, gt_mesh_data] = this.gt_obj_list_store.get_gt_mesh_data_by_name(obj_info["name"])
        if (gt_mesh_ind === null || gt_mesh_data === null) {
            return;
        }
        var gt_mesh_path = `${this.gt_mesh_root_path}/${gt_mesh_data["path"]}`;
        this.labeler_mesh_list_store.load_mesh(
            gt_mesh_path, gt_mesh_data["name"], obj_info["position"], obj_info["orientation"]);
    }

    add_mesh_handler(mesh, mesh_index) {
        this.add_mesh_callback_list.forEach(
            callback => callback(mesh, mesh_index)
        );
    }

    register_add_mesh_callback(callback) {
        this.add_mesh_callback_list.push(callback);
    }

    save_button_click_handler() {
        this.save_button_click_callback_list.forEach(
            callback => callback()
        );
    }

    register_save_button_click_callback(callback) {
        this.save_button_click_callback_list.push(callback);
    }


    save_and_render_button_click_handler() {
        this.save_and_render_button_click_callback_list.forEach(
            callback => callback()
        );
    }

    register_save_and_render_button_click_callback(callback) {
        this.save_and_render_button_click_callback_list.push(callback);
    }

    get_icp_button_click_handler(obj_info_index) {
        this.labeler_mesh_list_store.get_icp_button_click_handler(obj_info_index);
    }

    toggle_vis_button_click_handler(obj_info_index) {
        this.labeler_mesh_list_store.toggle_vis_button_click_handler(obj_info_index);
    }

}

export { LabelerMeshListController };