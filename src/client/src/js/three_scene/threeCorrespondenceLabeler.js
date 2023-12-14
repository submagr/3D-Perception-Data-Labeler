import * as THREE from "three";
import {
    OBJLoader
} from "three/examples/jsm/loaders/OBJLoader";

import { ThreeScene } from "./threeScene";
import { set_three_obj_props, get_dom_el_by_id, get_colors } from "./utils";


class ThreeCorrespondenceLabeler extends ThreeScene {
    constructor(
        canvas_id, add_transform_controls, gt_json_path, gt_meshes_root,
        obj_selector_el_id,
        obj_corr_marker_list_el_id,
        obj_corr_add_el_id,
        obj_corr_edit_el_id,
        obj_corr_delete_el_id,
    ) {
        /*
        ThreeLabeler for choosing the correspondence points on the gt meshes. User will then choose the same correspondence points
        on the scene point-cloud and thus help in estimating the initial object pose in the scene.
        @param canvas_id: string
        @param add_transform_controls: boolean
        @param gt_json_path: string - path to the json file containing the ground truth meshes. List[{path: string, name: string}]
        @param gt_meshes_root: string - path to the folder containing the meshes (gt_json[ind]["path"] will be appended with this)
        @param obj_selector_el_id: string - id of the select element to be used for selecting the object to be displayed
        @param obj_correspondence_selector_el_id: string - id of the select element to be used for selecting the correspondence points
        */
        super(canvas_id, add_transform_controls);

        var obj_selector_el = get_dom_el_by_id(obj_selector_el_id);
        this.gt_meshes_root = gt_meshes_root;

        // Add the onchange listener to the object selector
        var self = this;
        obj_selector_el.addEventListener("change", function () {
            // Inside here, `this` variable will be the element user selected
            self.load_selected_object(this);
        })

        // gt_meshes_data: list of dict of mesh data {name, path}
        this.gt_meshes_data = undefined;
        // gt_meshes: list of cached three meshes (lazy loaded)
        this.gt_meshes = [];
        // Read gt meshes data from the json file.
        this.corrs = [];  // list of (list of correspondence points) for each object
        fetch(gt_json_path)
            .then(response => response.json())
            .then(meshes => {
                for (var i = 0; i < meshes.length; i++) {
                    var opt = document.createElement("option");
                    opt.value = i;
                    opt.innerHTML = meshes[i]["name"];
                    obj_selector_el.appendChild(opt);
                    this.gt_meshes.push(undefined);
                }
                this.gt_meshes_data = meshes;
            });

        // loaded_obj_index: index of the loaded mesh in the gt_meshes
        this.loaded_obj_index = undefined;

        // Add event listener for object correspondence add new button
        var obj_corr_marker_list_el = get_dom_el_by_id(obj_corr_marker_list_el_id);
        var obj_corr_add_el = get_dom_el_by_id(obj_corr_add_el_id);

        this.corr_counter = 0;
        this.corr_colors = get_colors();
        this.corr_markers = [];
        obj_corr_add_el.addEventListener("click", function () {
            // Add new element to it's parent
            var new_el = document.createElement("option");
            // - add text
            new_el.value = self.corr_counter;
            var color = self.corr_colors[self.corr_counter % self.corr_colors.length]
            new_el.innerHTML = `Corr ${self.corr_counter} (${color})`;
            // - add color
            new_el.style.backgroundColor = color;
            // - add to list
            obj_corr_marker_list_el.append(new_el);
            // - change the selected element to this
            obj_corr_marker_list_el.value = self.corr_counter;

            // Add new marker
            const sphereGeometry = new THREE.SphereGeometry(0.005, 32, 32);
            const sphereMaterial = new THREE.MeshBasicMaterial({ color: color });
            var marker = new THREE.Mesh(sphereGeometry, sphereMaterial);
            self.corr_markers.push(marker);

            self.corr_counter = self.corr_counter + 1;
        });

        // Now when the add button is clicked, we need to add this new sphere to the scene.
        // And make the edit button activated as well. Moreover, we need to change the selection.

        document.addEventListener('pointermove', this.onPointerMove.bind(this));


        const threshold = 0.001;
        this.raycaster = new THREE.Raycaster();
        this.raycaster.params.Points.threshold = threshold;
        this.pointer = new THREE.Vector2();
    }

    onPointerMove(event) {
        if (event.target === this.canvas) {
            var rect = event.target.getBoundingClientRect();
            this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1; //x position within the element.
            this.pointer.y = - ((event.clientY - rect.top) / rect.height) * 2 + 1;  //y position within the element.
        } else {
            this.pointer.x = undefined;
            this.pointer.y = undefined;
        }
    }

    animation_logic() {
        if (this.loaded_obj_index !== undefined) {
            var loaded_obj = this.gt_meshes[this.loaded_obj_index];
            this.camera.updateMatrixWorld();

            this.raycaster.setFromCamera(this.pointer, this.camera);

            const intersections = this.raycaster.intersectObjects([loaded_obj], true);
            var intersection;
            for (var i = 0; i < intersections.length; i++) {
                var mesh_found = (intersections[i].object === loaded_obj);
                if (!mesh_found) {
                    loaded_obj.traverse(function (child) {
                        if (child.isMesh && intersections[i].object === child) {
                            mesh_found = true;
                            return false;
                        }
                    });
                }
                if (mesh_found) {
                    intersection = intersections[i];
                }
            }
            // find the loaded obj inside the intersection
            if (intersection !== undefined) {
                this.sphere.position.set(intersection.point.x, intersection.point.y, intersection.point.z);
            }
        }
    }

    load_selected_object(selected_el) {
        /* Load the selected object from the gt_meshes_data. Removes the previous
        selected object if any.*/
        var obj_index = parseInt(selected_el.value);
        var mesh_path = `${this.gt_meshes_root}/${this.gt_meshes_data[obj_index]["path"]}`;

        var obj_load_promise;
        if (this.gt_meshes[obj_index] === undefined) {
            const loader = new OBJLoader();  // TODO: should we create new objloader every time?
            var material = new THREE.MeshPhongMaterial({
                color: "gray",
            });
            obj_load_promise = new Promise((resolve, reject) => {
                loader.load(
                    mesh_path,
                    // called when the resource is loaded
                    (obj_mesh) => {
                        set_three_obj_props(
                            obj_mesh,
                            [0, 0, 0],
                            [0, 0, 0, 1],
                            material,
                            (obj_mesh) => {
                                this.gt_meshes[obj_index] = obj_mesh;
                                resolve(obj_mesh);
                            }
                        );
                    },
                    // called when the resource is being loaded
                    null,
                    // called when the loading has errors
                    (err) => { reject(err); }
                );
            });
        } else {
            obj_load_promise = Promise.resolve(this.gt_meshes[obj_index]);
        }

        obj_load_promise
            .then(obj_mesh => {
                // Remove the previously oaded object if any
                if (this.loaded_obj_index !== undefined) {
                    this.scene.remove(this.gt_meshes[this.loaded_obj_index]);
                    this.loaded_obj_index = undefined;
                }
                this.add(obj_mesh);
                this.loaded_obj_index = obj_index;
            })
            .catch(err => { console.error(err) });
    }
}

export { ThreeCorrespondenceLabeler };