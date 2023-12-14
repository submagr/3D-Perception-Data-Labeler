import { get_dom_el_by_id } from "./utils";

class PointCloudViewer {
    constructor(toggle_pc_el_id) {
        this.toggle_pc_el = get_dom_el_by_id(toggle_pc_el_id);
        var self = this;
        this.toggle_pc_el.addEventListener("click", function (event) {
            self.toggle_pc_click_handler();
        });
        this.toggle_pc_click_handler_callback_list = [];
    }

    toggle_pc_click_handler() {
        this.toggle_pc_click_handler_callback_list.forEach(
            callback => callback()
        );
    }

    register_toggle_pc_click_callback(callback) {
        this.toggle_pc_click_handler_callback_list.push(callback);
    }
}

export { PointCloudViewer };