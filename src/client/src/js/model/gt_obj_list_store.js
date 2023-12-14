class GTObjListStore {
    constructor(gt_json_path) {
        // Load the gt meshes json file.
        this._gt_meshes_data = {};
        fetch(gt_json_path)
            .then(response => response.json())
            .then(meshes_data => {
                for (var i = 0; i < meshes_data.length; i++) {
                    this.add_gt_mesh_data(meshes_data[i], i);
                }
            })

        this.gt_mesh_update_callbacks = [];
    }

    add_gt_mesh_data(gt_mesh_data, gt_mesh_index) {
        this._gt_meshes_data[gt_mesh_index] = gt_mesh_data
        this.gt_mesh_update_callbacks.forEach(
            callback => callback(
                gt_mesh_data,
                gt_mesh_index
            )
        );
    }

    get_gt_meshes_data() {
        return this._gt_meshes_data;
    }

    get_gt_mesh_data_at_ind(ind) {
        return (this._gt_meshes_data.hasOwnProperty(ind)) ? this._gt_meshes_data[ind] : null;
    }

    get_gt_mesh_data_by_name(name) {
        var req_index = null;
        var req_data = null;
        var gt_meshes_data = this.get_gt_meshes_data();
        for (var ind in gt_meshes_data) {
            if (
                gt_meshes_data.hasOwnProperty(ind)
                && gt_meshes_data[ind]["name"] === name
            ) {
                req_index = ind;
                req_data = gt_meshes_data[ind];
                break;
            }
        }
        return [req_index, req_data];
    }

    register_gt_mesh_update_callback(callback) {
        this.gt_mesh_update_callbacks.push(callback);
    }

}

export { GTObjListStore };