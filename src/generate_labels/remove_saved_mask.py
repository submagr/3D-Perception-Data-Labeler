from pathlib import Path
import pickle
from collections import namedtuple
import numpy as np
import json
from matplotlib import pyplot as plt
import constant_paths
from utils.render_utils import extract_masks


def main():
    data_dir = constant_paths.get_data_dir_path()
    gt_meshes_dir = constant_paths.get_gt_meshes_path()
    get_child_dirs = lambda path: [x for x in path.iterdir() if x.is_dir()]
    for scene_dir in get_child_dirs(data_dir):
        if not scene_dir.name.startswith("scene_"):
            continue
        # if scene_dir.name in []:
        #     print("Ignoring scene ", scene_dir.name)
        #     continue
        print("========================")
        print(scene_dir.name)

        new_json_path = (
            scene_dir
            / "labels_object_set_0__lighting_0__view_3_object_set_info.pkl.json"
        )
        if new_json_path.exists():
            print("New Json is alreay present. Continuing.")
            continue
        json_path = scene_dir / "labels_object_set_0__lighting_0__view_3.pkl.json"
        if not json_path.exists():
            print("Scene not labelled: ", json_path, ". Ignoring.")
            continue
        with open(json_path, "r") as fp:
            updated_scene = json.load(fp)
        updated_objects = updated_scene["objects"]
        present_objects = list(range(len(updated_objects)))  # objects in scene
        object_set_dirs = [
            o for o in scene_dir.iterdir() if o.name.startswith("object_set_")
        ]
        object_set_dirs = sorted(object_set_dirs, key=lambda x: x.name)
        prev_set_rgb, curr_set_rgb = None, None
        for object_set_dir_index, object_set_dir in enumerate(object_set_dirs):
            view_pkl = object_set_dir / "lighting_0" / "view_1.pkl"
            # Let's load the aligned meshes and the original pointcloud
            # Now, I want to render it and visualize it.
            with open(view_pkl, "rb") as fp:
                view_data = pickle.load(fp)

            MyCameraData = namedtuple(
                "MyCameraData", ["rgb", "depth", "camera_k", "camera_extr"]
            )
            my_camera_data = MyCameraData(
                view_data["rgb"],
                view_data["depth"],
                view_data["camera_intrinsics"],
                np.linalg.inv(view_data["tag_pose"]),
            )
            data, mask_object_indices = extract_masks(
                json_path,
                my_camera_data,
                None,
                gt_meshes_dir,
                str(view_pkl),
                visualize=False,
            )
            # Let's visualize all of this now.
            curr_set_rgb = view_data["rgb"]
            ncols = 3
            nrows = np.ceil((len(data) + 2) / ncols).astype(int)
            fig, ax = plt.subplots(nrows, ncols, squeeze=False, figsize=(30, 30))
            ax[0, 0].axis("off")
            ax[0, 0].set_title("Previous set")
            if prev_set_rgb is not None:
                ax[0, 0].imshow(prev_set_rgb)
            ax[0, 1].axis("off")
            ax[0, 1].set_title("Current set")
            if curr_set_rgb is not None:
                ax[0, 1].imshow(curr_set_rgb)
            for i, data_i in enumerate(data):
                row = (i + 2) // ncols
                col = (i + 2) % ncols
                ax[row, col].imshow(curr_set_rgb)
                ax[row, col].imshow(data_i["mask_array"], alpha=0.3, cmap="jet")
                object_index = mask_object_indices[i]
                object_info = updated_objects[object_index]
                ax[row, col].set_title(
                    f"{object_info['name']}; {object_index}; isPresent: "
                    f"{object_index in present_objects}"
                )
                ax[row, col].axis("off")
            plt.suptitle(object_set_dir.name)
            plt.show()
            plt.close()
            prev_set_rgb = curr_set_rgb
            if object_set_dir_index != 0:
                print(
                    "What objects were removed in this object set (seperated by comma)?"
                )
                objects_removed = input()
                objects_removed = [
                    int(x) for x in objects_removed.split(",") if x.isdigit()
                ]
                for object_removed in objects_removed:
                    print(
                        f"{object_removed}:{updated_objects[object_removed]['name']} "
                        f"removed in {object_set_dir.name}"
                    )
                    present_objects.remove(object_removed)

            # Ok. Now I have the data. What else?
            # Let's write the code on how this data was generated.
            for obj_index in present_objects:
                if "present_in_object_set" not in updated_objects[obj_index]:
                    updated_objects[obj_index]["present_in_object_set"] = []
                updated_objects[obj_index]["present_in_object_set"].append(
                    object_set_dir.name
                )

        updated_scene["objects"] = updated_objects
        with open(new_json_path, "w") as fp:
            json.dump(updated_scene, fp)
        print("New json saved at path: ", new_json_path)


if __name__ == "__main__":
    main()
