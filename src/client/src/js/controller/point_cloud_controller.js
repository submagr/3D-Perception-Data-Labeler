class PointCloudController {
    constructor(point_cloud_store, point_cloud_viewer) {
        this.point_cloud_store = point_cloud_store;
        this.point_cloud_viewer = point_cloud_viewer;
        this.point_cloud_store.register_add_pc_callback(this.add_pc_handler.bind(this));
        var curr_pc_list = this.point_cloud_store.get_pc_list();
        for (var i = 0; i < curr_pc_list.length; i++) {
            this.add_pc_handler(curr_pc_list[i], i);
        }
        this.add_pc_callback_list = [];
        this.point_cloud_viewer.register_toggle_pc_click_callback(
            this.point_cloud_store.toggle_pc_click_handler.bind(this.point_cloud_store)
        );
    }

    add_pc_handler(pc, pc_index) {
        this.add_pc_callback_list.forEach(
            callback => callback(pc, pc_index)
        );
    }

    register_add_pc_callback(callback) {
        this.add_pc_callback_list.push(callback);
    }
}

export { PointCloudController };