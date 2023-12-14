import { get_dom_el_by_id } from "./utils";

class ObjListViewer {
    constructor(obj_list_table_id, obj_list_el_radio_id) {
        this.obj_list_table = get_dom_el_by_id(obj_list_table_id);
        this.obj_list_el_radio_id = obj_list_el_radio_id;
        this.obj_selection_change_callback_list = [];
        this.get_icp_button_click_callback_list = [];
        this.toggle_vis_button_click_callback_list = [];
    }

    add_obj_info(obj_info, obj_info_index) {
        // Create a new row
        var row = document.createElement("tr");
        // Add metadata to the row
        row.dataset.obj_info_index = obj_info_index;
        row.dataset.obj_info_name = obj_info["name"];

        // - add the radio button for selecting the object
        var cell = document.createElement("td");
        var radio_input = document.createElement("input");
        radio_input.setAttribute("type", "radio");
        radio_input.setAttribute("name", "active_obj");
        radio_input.setAttribute("id", this.obj_list_el_radio_id);
        var self = this;
        radio_input.addEventListener("click", function (event) {
            self.obj_radio_button_selected_handler(event);
        });
        cell.append(radio_input);
        row.append(cell);

        // - add obj index and name
        var cell = document.createElement("td");
        cell.innerHTML = `${obj_info_index} ${obj_info["name"]}`;
        row.append(cell);
        // - add "get icp" button
        var cell = document.createElement("td");
        var button = document.createElement("button");
        button.innerHTML = "Get ICP"
        button.addEventListener("click", function (event) {
            self.get_icp_button_click_handler(event);
        });
        cell.append(button);
        row.append(cell);

        // - add obj toggle visibility
        var cell = document.createElement("td");
        var button = document.createElement("button");
        button.innerHTML = "Toggle mesh visibility"
        button.addEventListener("click", function (event) {
            self.toggle_vis_button_click_handler(event);
        });
        cell.append(button);
        row.append(cell);

        // Add row to the table 
        this.obj_list_table.append(row);
    }

    obj_radio_button_selected_handler(event) {
        var radio_el = event.target
        var row = radio_el.parentElement.parentElement;
        var obj_info_index = parseInt(row.dataset.obj_info_index);
        this.obj_selection_change_callback_list.forEach(
            callback => callback(obj_info_index)
        );
    }

    register_obj_selection_change_callback(callback) {
        this.obj_selection_change_callback_list.push(callback);
    }

    get_obj_info_index_from_table_cell_el(cell_el) {
        var row = cell_el.parentElement.parentElement;
        var obj_info_index = parseInt(row.dataset.obj_info_index);
        return obj_info_index;
    }
    get_icp_button_click_handler(event) {
        var obj_info_index = this.get_obj_info_index_from_table_cell_el(event.target)
        this.get_icp_button_click_callback_list.forEach(
            callback => callback(obj_info_index)
        );
    }

    register_get_icp_button_click_callback(callback) {
        this.get_icp_button_click_callback_list.push(callback);
    }

    toggle_vis_button_click_handler(event) {
        var obj_info_index = this.get_obj_info_index_from_table_cell_el(event.target)
        this.toggle_vis_button_click_callback_list.forEach(
            callback => callback(obj_info_index)
        );
    }

    register_toggle_vis_button_click_callback(callback) {
        this.toggle_vis_button_click_callback_list.push(callback);
    }
}

export { ObjListViewer };