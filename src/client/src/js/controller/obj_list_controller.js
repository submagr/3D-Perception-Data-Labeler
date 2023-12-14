class ObjListController {
    constructor(obj_list_store, gt_obj_list_store, obj_list_viewer) {
        this.obj_list_store = obj_list_store;
        this.gt_obj_list_store = gt_obj_list_store;
        this.obj_list_viewer = obj_list_viewer;

        this.obj_list_store.register_obj_info_list_add_callback(
            this.obj_info_list_add_callback.bind(this)
        );
        var curr_obj_info_list = this.obj_list_store.get_obj_info_list();
        for (var i = 0; i < curr_obj_info_list.length; i++) {
            this.obj_info_list_add_callback(curr_obj_info_list[i], i);
        }

        this.obj_list_viewer.register_obj_selection_change_callback(
            this.obj_selection_change_handler.bind(this)
        );
        this.obj_selection_change_callback_list = [];

        this.obj_list_viewer.register_get_icp_button_click_callback(
            this.get_icp_button_click_handler.bind(this)
        );
        this.get_icp_button_click_callback_list = [];

        this.obj_list_viewer.register_toggle_vis_button_click_callback(
            this.toggle_vis_button_click_handler.bind(this)
        );
        this.toggle_vis_button_click_callback_list = [];
    }

    obj_info_list_add_callback(obj_info, obj_info_index) {
        this.obj_list_viewer.add_obj_info(obj_info, obj_info_index);
    }

    add_to_obj_info_list_callback(gt_mesh_index) {
        // use gt_mesh_store to get the appropriate obj info;
        if (gt_mesh_index === null) {
            return;
        }

        var gt_mesh_data = this.gt_obj_list_store.get_gt_mesh_data_at_ind(gt_mesh_index);
        var obj_info = {
            name: gt_mesh_data["name"],
            orientation: null,
            position: null,
        };
        this.obj_list_store.add_to_obj_info_list(obj_info);
    }

    register_obj_selection_change_callback(callback) {
        this.obj_selection_change_callback_list.push(callback);
    }

    obj_selection_change_handler(obj_info_index) {
        this.obj_selection_change_callback_list.forEach(
            callback => callback(obj_info_index)
        );
    }

    get_icp_button_click_handler(obj_info_index) {
        this.get_icp_button_click_callback_list.forEach(
            callback => callback(obj_info_index)
        );
    }

    register_get_icp_button_click_callback(callback) {
        this.get_icp_button_click_callback_list.push(callback);
    }

    toggle_vis_button_click_handler(obj_info_index) {
        this.toggle_vis_button_click_callback_list.forEach(
            callback => callback(obj_info_index)
        );
    }

    register_toggle_vis_button_click_callback(callback) {
        this.toggle_vis_button_click_callback_list.push(callback);
    }
}

export { ObjListController };