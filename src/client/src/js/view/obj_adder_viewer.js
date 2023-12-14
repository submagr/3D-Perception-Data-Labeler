import {get_dom_el_by_id} from './utils';

class ObjAdderViewer {
    constructor (obj_selector_id, obj_add_id) {
        this.obj_selector = get_dom_el_by_id(obj_selector_id);
        this.obj_add_button = get_dom_el_by_id(obj_add_id);
    }

    add_gt_mesh_data_to_selector_list (gt_mesh_data, gt_mesh_index) {
        var option_el = document.createElement("option");  
        option_el.value = gt_mesh_index;
        option_el.innerHTML = gt_mesh_data.name;
        this.obj_selector.append(option_el);
    }

    get_current_selection () {
        var gt_mesh_index = this.obj_selector.value;
        if (gt_mesh_index === undefined) {
            return null;
        }
        gt_mesh_index = parseInt(gt_mesh_index);
        if (gt_mesh_index === -1) {
            return null;
        }
        return gt_mesh_index;
    }
}

export {ObjAdderViewer};