/* Store for object meshes inside the main labeler*/
import * as THREE from "three";
import {
    OBJLoader
} from "three/examples/jsm/loaders/OBJLoader";
import {
    get_dom_el_by_id, get_obj_states_materials, apply_mesh_material
} from "../view/utils";
import { send_json_request, toggle_three_mesh_vis } from "./utils";


class LabelerMeshListStore {
    constructor(server_url, scene_index) {
        this.meshes = [];
        this.add_mesh_callback_list = [];
        this.server_url = server_url;
        this.scene_index = scene_index;
        this.save_scene_url = `${server_url}/save_scene?scene=${this.scene_index}`;
        this.save_and_render_scene_url = `${server_url}/save_and_render_scene?scene=${this.scene_index}`;
        this.get_icp_url = `${server_url}/get_icp`;
        this.get_img_el();
        this.inactive_obj_material = get_obj_states_materials()["inactive"];
    }

    add_mesh(mesh, mesh_name, pos, ori) {
        apply_mesh_material(mesh, this.inactive_obj_material);
        if (pos) {
            mesh.position.set(pos[0], pos[1], pos[2]);
        }
        if (ori) {
            const orientation = new THREE.Quaternion(
                ori[0], ori[1], ori[2], ori[3]);
            mesh.setRotationFromQuaternion(orientation);
        }

        this.meshes.push({
            "mesh": mesh,
            "name": mesh_name,
        });
        this.add_mesh_callback_list.forEach(
            callback => callback(
                mesh,
                this.meshes.length - 1
            )
        )
    }

    register_add_mesh_callback(callback) {
        this.add_mesh_callback_list.push(callback);
    }

    load_mesh(mesh_path, mesh_name, pos, ori) {
        const loader = new OBJLoader();
        mesh_path = `${this.server_url}/${mesh_path}`;
        loader.load(
            mesh_path,
            (mesh) => {
                this.add_mesh(mesh, mesh_name, pos, ori);
            },
            null, null
        )
    }

    save_button_click_handler() {
        this.save_scene_data(false, null);
    }

    get_img_el() {
        let img_el = get_dom_el_by_id("mask-img", false);
        if (img_el === null || img_el === undefined) {
            img_el = document.createElement("img")
            let base_src = `/scene/${this.scene_index}/mask.png`;
            img_el.setAttribute("src", base_src);
            img_el.setAttribute("id", "mask-img");
            img_el.setAttribute("data-basesrc", base_src);
            let top_div_el = get_dom_el_by_id("top")
            top_div_el.append(img_el);
        }
        return img_el;
    }

    render_data_handler(result) {
        console.log("Render results received: ", result);
        let img_el = this.get_img_el();
        let base_src = img_el.dataset.basesrc;
        img_el.src = `${base_src}?rand=${Math.random()}`;
    }

    save_and_render_button_click_handler() {
        this.save_scene_data(true, this.render_data_handler.bind(this));
    }

    get_scene_data() {
        // let's get the latest mesh data from the store.
        let objs_data = [];
        for (var i = 0; i < this.meshes.length; i++) {
            let obj_data = {};
            obj_data["name"] = this.meshes[i]["name"];
            let mesh = this.meshes[i]["mesh"].children[0];
            let quat = mesh.getWorldQuaternion(new THREE.Quaternion());
            obj_data["orientation"] = [quat.x, quat.y, quat.z, quat.w];
            let pos = mesh.getWorldPosition(new THREE.Vector3());
            obj_data["position"] = [pos.x, pos.y, pos.z];
            objs_data.push(obj_data);
        }
        let scene_data = {
            "objects": objs_data
        }
        return scene_data;
    }

    save_scene_data(render, render_callback) {
        let scene_data = this.get_scene_data();
        let scene_json = JSON.stringify(scene_data);
        console.log("Sending scene json: ", scene_json);
        if (render) {
            send_json_request(this.save_and_render_scene_url, scene_json)
                .then(result => render_callback(result))
                .catch(error => console.log('error', error));
        } else {
            send_json_request(this.save_scene_url, scene_json)
                .then(result => result.text())
                .then(result => {
                    console.log(result);
                    alert("Scene saved!");
                })
                .catch(error => console.log('error', error));
        }
    }

    get_icp_button_click_handler(obj_info_index) {
        console.log(`ICP-Button clicked for ${obj_info_index} - ${this.meshes[obj_info_index]["name"]}`);
        // Now, let's send the object pose and scene index to the server
        let icp_data = {};
        icp_data["scene"] = this.scene_index;
        icp_data["object"] = {}
        let obj_data = this.meshes[obj_info_index]
        icp_data["object"]["name"] = obj_data["name"];
        let mesh = obj_data["mesh"];
        let quat = mesh.getWorldQuaternion(new THREE.Quaternion());
        icp_data["object"]["orientation"] = [quat.x, quat.y, quat.z, quat.w];
        let pos = mesh.getWorldPosition(new THREE.Vector3());
        icp_data["object"]["position"] = [pos.x, pos.y, pos.z];

        let icp_data_json = JSON.stringify(icp_data);
        send_json_request(this.get_icp_url, icp_data_json)
            .then(result => result.json())
            .then(result => {
                console.log(result);
                let pos = result["position"]
                mesh.position.set(pos[0], pos[1], pos[2]);
                let ori = result["orientation"]
                const orientation = new THREE.Quaternion(
                    ori[0], ori[1], ori[2], ori[3]);
                mesh.setRotationFromQuaternion(orientation);
            })
            .catch(error => console.log('error', error));
    }

    toggle_vis_button_click_handler (obj_info_index) {
        let mesh = this.meshes[obj_info_index]["mesh"];
        toggle_three_mesh_vis(mesh);
    }
}

export { LabelerMeshListStore };