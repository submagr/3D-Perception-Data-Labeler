import * as THREE from "three";
import { ThreeViewerBase } from "./three_viewer_base.js";
import {get_obj_states_materials, apply_mesh_material} from "./utils.js";


class ThreeLabelerViewer extends ThreeViewerBase {
    constructor(canvas_id) {
        super(canvas_id);
        this.pc_dict = {};
        this.mesh_dict = {};
        this.active_obj_index = null;

        this.obj_states_materials = get_obj_states_materials();
    }

    add_pc_handler(pc, pc_index) {
        this.pc_dict[pc_index] = pc;
        this.scene.add(pc);
    }

    add_mesh_handler(mesh, mesh_index) {
        this.mesh_dict[mesh_index] = mesh;
        this.scene.add(mesh);
    }

    active_obj_change_handler(obj_info_index) {
        if (obj_info_index === null || obj_info_index === undefined || this.mesh_dict[obj_info_index] === undefined) {
            console.error("obj_info_index is null or undefined");
            return;
        }

        if (this.active_obj_index !== null) {
            // - change color to inactive
            var obj = this.mesh_dict[this.active_obj_index];
            apply_mesh_material(obj, this.obj_states_materials["inactive"]);
        }
        var obj = this.mesh_dict[obj_info_index];
        apply_mesh_material(obj, this.obj_states_materials["active"]); 
        this.active_obj_index = obj_info_index;
        this.transformControls.attach(obj);
    }
}

export { ThreeLabelerViewer };