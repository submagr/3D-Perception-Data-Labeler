import * as THREE from "three";
import {
    OrbitControls
} from "three/examples/jsm/controls/OrbitControls";
import {
    TransformControls
} from "three/examples/jsm/controls/TransformControls.js";

class ThreeViewerBase {
    constructor(canvas_id) {
        /*
            canvas_id: string - DOM id of the canvas element to render to
            add_transfrom_controls: boolean - whether to add transform controls
        */
        this.canvas = document.getElementById(canvas_id);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas });

        var fov = 45;
        var aspect = 2;
        var near = 0.1;
        var far = 100;
        this.camera = new THREE.PerspectiveCamera(fov, aspect, near, far);
        this.camera.up.set(0, 0, 1);
        this.camera.position.set(0.8, 0, 0.6);

        this.orbitControl = new OrbitControls(this.camera, this.canvas);
        this.orbitControl.target.set(0, 0, 0);
        this.orbitControl.update();

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x66645d);

        this.transformControls = new TransformControls(this.camera, this.canvas);
        var self = this;
        this.transformControls.addEventListener("dragging-changed", function (event) {
            self.orbitControl.enabled = !event.value;
        })
        this.scene.add(this.transformControls);
        window.addEventListener("keydown", function(event) {
            self.transform_controls_key_down_handler(event); 
        });

        const ambiLight = new THREE.AmbientLight(0xf0f0f0);
        this.scene.add(ambiLight);
        const light = new THREE.SpotLight(0xffffff, 0.5);
        light.position.set(0, 0, 200);
        light.angle = Math.PI / 5;
        light.castShadow = true;
        light.shadow.camera.near = 200;
        light.shadow.camera.far = 2000;
        light.shadow.bias = - 0.000222;
        light.shadow.mapSize.width = 1024;
        light.shadow.mapSize.height = 1024;
        this.scene.add(light);
    }

    animation_logic() {
        /* any class specific animation logic */
    }

    animate() {
        /* Boilerplate animation */
        if (resizeRendererToDisplaySize(this.renderer)) {
            this.camera.aspect = this.canvas.clientWidth / this.canvas.clientHeight;
            this.camera.updateProjectionMatrix();
        }
        this.animation_logic();
        this.renderer.render(this.scene, this.camera);
    }

    add(ent) {
        this.scene.add(ent);
    }

    transform_controls_key_down_handler(event) {
        switch (event.keyCode) {
            case 81: // Q
                this.transformControls.setSpace(
                    this.transformControls.space === "local" ? "world" : "local");
                break;
            case 87: // W
                this.transformControls.setMode("translate");
                break;
            case 69: // E
                this.transformControls.setMode("rotate");
                break;
        }
    }

}


function resizeRendererToDisplaySize(renderer) {
    const canvas = renderer.domElement;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const needResize = canvas.width != width || canvas.height != height;
    if (needResize) {
        renderer.setSize(width, height, false);
    }
    return needResize;
}

function animate_three_scenes(three_scenes) {
    function animate() {
        requestAnimationFrame(animate);
        for (var i = 0; i < three_scenes.length; i++) {
            three_scenes[i].animate();
        }
    }
    animate();
};


export { ThreeViewerBase, animate_three_scenes};