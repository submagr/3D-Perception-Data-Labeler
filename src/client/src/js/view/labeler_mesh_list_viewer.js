import { get_dom_el_by_id } from "./utils";

class LabelerMeshListViewer {
    constructor(save_button_id, save_and_render_button_id) {
        this.save_button = get_dom_el_by_id(save_button_id);
        var self = this;
        // save-button
        this.save_button.addEventListener("click", function(event) {
            self.save_button_click_handler(event);    
        })
        this.save_button_click_callback_list = [];
        // save-and-render-button
        this.save_and_render_button = get_dom_el_by_id(save_and_render_button_id);
        this.save_and_render_button.addEventListener("click", function(event) {
            self.save_and_render_button_click_handler(event);    
        })
        this.save_and_render_button_click_callback_list = [];

    }

    register_save_button_click_callback (callback) {
        this.save_button_click_callback_list.push(callback);
    }

    save_button_click_handler(event) {
        this.save_button_click_callback_list.forEach(
            callback => callback()
        );
    }

    register_save_and_render_button_click_callback (callback) {
        this.save_and_render_button_click_callback_list.push(callback);
    }

    save_and_render_button_click_handler(event) {
        this.save_and_render_button_click_callback_list.forEach(
            callback => callback()
        );
    }
}

export { LabelerMeshListViewer };