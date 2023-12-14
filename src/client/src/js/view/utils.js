import * as THREE from "three";

function get_dom_el_by_id(id, throw_exception = true) {
    var el = document.getElementById(id);
    if (!el && throw_exception) {
        throw `Could not find element with id: ${id}`;
    }
    return el;
}


function get_mesh_material(r, g, b) {
    const color = new THREE.Color(r, g, b);
    const material = new THREE.MeshPhongMaterial({ color: color });
    return material;
}

function apply_mesh_material(mesh, material) {
    mesh.traverse(function (child) {
        if (child.isMesh) {
            child.material = material;
        }
    });
}

function get_obj_states_materials() {
    return {
        "inactive": get_mesh_material(0.502, 0.502, 0.502),
        "active": get_mesh_material(0.157, 0.498, 0.612)
    }
}

export { get_dom_el_by_id, get_mesh_material, apply_mesh_material, get_obj_states_materials };