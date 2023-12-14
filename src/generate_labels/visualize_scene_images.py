import sys
from pathlib import Path
root_path = Path(__file__).parent.parent.absolute()
print("Adding to python path: ", root_path)
sys.path = [str(root_path)] + sys.path

import re
import pickle
from matplotlib import pyplot as plt
import constant_paths


def get_user_key_press(prompt_msg, key_details):
    key = None
    while True:
        print(prompt_msg)
        for i, (key, value) in enumerate(key_details.items()):
            print(f"({i}) Press {key} for {value}")
        key = input()
        if key in key_details:
            break
        else:
            print(f"Invalid key '{key}' pressed. Try again")
    return key


def visualize_views():
    data_dir = constant_paths.get_data_dir_path()
    view_pkl_pattern = re.compile("view_\d+\.pkl")
    # while True:
    #     print("Enter scene index to visualize:")
    #     scene_index = input()
    #     scene_dir = data_dir / f"scene_{scene_index}"
    for scene_dir in data_dir.glob("scene_*"):
        if not scene_dir.exists():
            print(f"{scene_dir} does not exist")
            continue
        # view_root = scene_dir / "object_set_0" / "lighting_0"
        view_root = scene_dir
        view_pkls = [
            x for x in view_root.rglob("view_*.pkl") if view_pkl_pattern.search(x.name)
        ]
        for view_pkl in view_pkls:
            with open(view_pkl, "rb") as fp:
                data = pickle.load(fp)
            # plt.imshow(data["rgb"])
            # plt.show()
            plt.imsave(view_root / f"{view_pkl.stem}.png", data["rgb"])
            plt.close()
            print("Saved at ", view_root / f"{view_pkl.stem}.png")



def visualize_object_sets():
    data_dir = constant_paths.get_data_dir_path()
    while True:
        print("Enter scene index to visualize:")
        scene_index = input()
        scene_dir = data_dir / f"scene_{scene_index}"
        if not scene_dir.exists():
            print(f"{scene_dir} does not exist")
            continue
        view_index = 0
        while True:
            prev_view_rgb = None
            curr_view_rgb = None
            object_set_dirs = sorted(list(scene_dir.iterdir()), key=lambda x: x.name)
            for object_set_dir in object_set_dirs:
                if not object_set_dir.name.startswith("object_set_"):
                    continue
                view_pkl_path = object_set_dir / "lighting_0" / f"view_{view_index}.pkl"
                if not view_pkl_path.exists():
                    print(f"View {view_pkl_path} not found. Choose different view")
                    break
                with open(view_pkl_path, "rb") as fp:
                    view_data = pickle.load(fp)
                    curr_view_rgb = view_data["rgb"]
                _, ax = plt.subplots(1, 2)
                ax[0].set_title(f"Previous view")
                if prev_view_rgb is not None:
                    ax[0].imshow(prev_view_rgb)
                ax[1].set_title(f"Current view {object_set_dir.name}")
                if curr_view_rgb is not None:
                    ax[1].imshow(curr_view_rgb)
                plt.show()
                plt.close()
                prev_view_rgb = curr_view_rgb

            key = get_user_key_press(
                "Choose one of the following:",
                {
                    "y": f"visualize different view of the same scene {scene_index}",
                    "n": "choose different scene",
                },
            )
            if key == "y":
                print("Select view index:")
                view_index = input()
                continue
            else:
                break


def main():
    key = get_user_key_press(
        "Choose one of the following:",
        {"v": "visualize views", "o": "visualize object sets"},
    )
    if key == "o":
        visualize_object_sets()
    else:
        visualize_views()


if __name__ == "__main__":
    main()
