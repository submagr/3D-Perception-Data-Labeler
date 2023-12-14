class ObjAdderController {
    constructor(gt_meshes_store, obj_adder_viewer) {
        // This controller will have logic for hooking up model and itself.
        // And based on that, subsequently updating the view as well.
        this.gt_meshes_store = gt_meshes_store;
        this.obj_adder_viewer = obj_adder_viewer;

        this.gt_meshes_store.register_gt_mesh_update_callback(
            this.gt_mesh_update_callback.bind(this)
        );
        // Also, if there are any meshes already there, let's update them manually here.
        var curr_gt_mesh_data = this.gt_meshes_store.get_gt_meshes_data()
        for (var gt_mesh_index in curr_gt_mesh_data) {
            if (curr_gt_mesh_data.hasOwnProperty(gt_mesh_index)) {
                this.gt_mesh_update_callback(
                    curr_gt_mesh_data[gt_mesh_index],
                    gt_mesh_index
                );
            }
        }

        // Hook up the add button as well.
        var self = this;
        this.obj_adder_viewer.obj_add_button.addEventListener("click", function () {
            self.obj_add_handler();
        });
        this.obj_add_callbacks = [];
    }

    gt_mesh_update_callback(gt_mesh_data, gt_mesh_index) {
        // What should I do here? Update the view. Cool.
        // basically add the mesh to the list.
        this.obj_adder_viewer.add_gt_mesh_data_to_selector_list(gt_mesh_data, gt_mesh_index);
    }

    obj_add_handler() {
        // we also need to read the gt mesh data from the view.
        var selected_gt_mesh_ind = this.obj_adder_viewer.get_current_selection();
        if (selected_gt_mesh_ind !== null) {
            this.obj_add_callbacks.forEach(function (callback) {
                callback(selected_gt_mesh_ind);
            })
        }
    }

    register_obj_add_callback(callback) {
        this.obj_add_callbacks.push(callback);
    }
}

export { ObjAdderController };