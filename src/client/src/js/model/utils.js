import * as THREE from "three";
function send_json_request(url, json_str) {
    let myHeaders = new Headers();
    myHeaders.append("Content-Type", "application/json");
    let requestOptions = {
        method: 'POST',
        headers: myHeaders,
        body: json_str,
        redirect: 'follow'
    };
    return fetch(url, requestOptions);
}

function toggle_three_mesh_vis(obj) {
    obj.traverse(function (child) {
        if (child instanceof THREE.Object3D) {
            if (child.visible)
                child.visible = false;
            else
                child.visible = true;
        }
    });

}

export { send_json_request, toggle_three_mesh_vis };