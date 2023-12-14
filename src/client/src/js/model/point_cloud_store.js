import * as THREE from "three";
import {
    PLYLoader
} from "three/examples/jsm/loaders/PLYLoader";
import { toggle_three_mesh_vis } from "./utils";

class PointCloudStore {
    constructor(scene_ind) {
        this.pc_list = [];
        this.add_pc_callback_list = [];
        this.scene_ind = scene_ind;
    }

    load_pc() {
        const ply_path = `/scene/${this.scene_ind}/pcl/scene_pcl.ply`
        const loader = new PLYLoader();
        var self = this;
        loader.load(ply_path, function (geometry) {
            const material = new THREE.PointsMaterial({ size: 0.005, vertexColors: true });
            var pc = new THREE.Points(geometry, material);
            self.add_pc(pc);
        });
    }

    add_pc(pc) {
        this.pc_list.push(pc);
        this.add_pc_callback_list.forEach(
            callback => callback(
                pc,
                this.pc_list.length - 1
            )
        );
    }

    register_add_pc_callback(callback) {
        this.add_pc_callback_list.push(callback);
    }

    get_pc_list() {
        return this.pc_list
    }

    toggle_pc_click_handler() {
        for (var i=0; i<this.pc_list.length; i++) {
            var pc = this.pc_list[i];
            toggle_three_mesh_vis(pc);
        }
    }
}

export { PointCloudStore };