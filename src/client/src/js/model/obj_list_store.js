class ObjListStore {
    constructor(server_url, scene_ind) {
        this.scene_json_url = `${server_url}/get_scene_labels?scene=${scene_ind}`;
        this._obj_info_list = [];
        fetch(this.scene_json_url)
            .then(response => response.json())
            .then(scene_json => {
                var object_list = scene_json["objects"];
                object_list.forEach(obj_info => {
                    this.add_to_obj_info_list(obj_info);
                });
            });

        this.obj_info_list_add_callbacks = [];
    }

    add_to_obj_info_list(obj_info) {
        this._obj_info_list.push(obj_info);
        this.obj_info_list_add_callbacks.forEach(
            callback => callback(
                obj_info,
                this._obj_info_list.length - 1
            )
        );
    }

    get_obj_info_list() {
        return this._obj_info_list;
    }

    register_obj_info_list_add_callback(callback) {
        this.obj_info_list_add_callbacks.push(callback);
    }

}

export { ObjListStore };