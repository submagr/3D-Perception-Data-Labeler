import sys
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt
from generate_labels.utils.render_utils import extract_masks_helper, get_mask_rgb_save_path


def main():
    json_path, view_pkl, gt_meshes_dir = sys.argv[1:]
    json_path = Path(json_path)
    view_pkl = Path(view_pkl)
    gt_meshes_dir = Path(gt_meshes_dir)

    mask_save_path, mask_data, rgb = extract_masks_helper(
        (json_path, view_pkl, None, gt_meshes_dir)
    )

    # Iterate over data and generate one mask file
    # print("=======>FIXME<======= Using bad masking logic")
    mask_array = None
    mask_class_list = []
    for mask_data_i in mask_data:
        curr_mask_array = mask_data_i["mask_array"]
        mask_class = mask_data_i["class"]
        if mask_class not in mask_class_list:
            mask_class_list.append(mask_class)
        mask_class_index = mask_class_list.index(mask_class) + 1
        if mask_array is None:
            mask_array = curr_mask_array.astype(np.uint8) * mask_class_index
        else:
            valid_indices = np.where(curr_mask_array)
            mask_array[valid_indices] = (
                curr_mask_array.astype(np.uint8)[valid_indices] * mask_class_index
            )

    scene_dir = json_path.parent
    mask_save_path, rgb_save_path = get_mask_rgb_save_path(scene_dir)
    plt.imshow(rgb)
    plt.imshow(mask_array, alpha=0.3, cmap="jet")
    plt.savefig(str(mask_save_path))
    plt.close()
    plt.imshow(rgb)
    plt.savefig(str(rgb_save_path))
    plt.close()


if __name__ == "__main__":
    main()
