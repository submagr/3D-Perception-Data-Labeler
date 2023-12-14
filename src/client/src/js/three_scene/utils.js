import * as THREE from "three";

function set_three_obj_props(mesh, pos, quat, material, callback) {
    /* Set basic properties of the mesh
    @param mesh: THREE Mesh
    @param pos: [x, y, z] 
    @param quat: [x, y, z, w]
    @param material: THREE Material
    @param callback: callback function to call when mesh properties are set*/
    const orientation = new THREE.Quaternion(
        quat[0],
        quat[1],
        quat[2],
        quat[3],
    );
    mesh.setRotationFromQuaternion(orientation);
    mesh.traverse(function (child) {
        if (child.isMesh) {
            child.material = material;
        }
    });
    mesh.position.set(pos[0], pos[1], pos[2]);
    callback(mesh);
}

function set_three_obj_visibility(obj, is_visible) {
    obj.traverse ( function (child) {
        if (child instanceof THREE.Mesh) {
            child.visible = is_visible;
        }
    });
}

function get_colors() {
    return [
        'gray', 'brown', 'orange', 'blue', "red", "green", "skyblue", "yellow",
        "purple", "pink", "black", "white"
    ];
}

export { set_three_obj_props, set_three_obj_visibility, get_colors};