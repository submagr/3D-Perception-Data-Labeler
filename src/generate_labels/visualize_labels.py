from collections import defaultdict
from pathlib import Path
from shutil import rmtree
import pickle
from matplotlib import pyplot as plt
from tqdm import tqdm
from multiprocessing import Pool
import constant_paths
from utils.html_vis import visualize_helper


def visualize_pickle(args):
    view_pkl, mask_pkl, visualize_dir, i, root = args
    with open(view_pkl, "rb") as fp:
        view_data = pickle.load(fp)
    with open(mask_pkl, "rb") as fp:
        mask_data = pickle.load(fp)
    
    # Show rgb
    rgb_path = visualize_dir / f"{i}_rgb.png"
    plt.imsave(rgb_path, view_data["rgb"])
    visualize_path = {}
    visualize_path["path"] = str(view_pkl.relative_to(root))
    visualize_path["rgb"] = rgb_path
    # Show mask with class names
    class_counter = defaultdict(int)
    for mask_info in mask_data:
        plt.imshow(view_data["rgb"])
        plt.imshow(mask_info["mask_array"], alpha=0.5, cmap="jet")
        mask_class = mask_info["class"] 
        class_counter[mask_class] += 1
        mask_name = f"{mask_info['class']}_{class_counter[mask_class]}"
        mask_path = visualize_dir / f"{i}_{mask_name}.png"
        plt.savefig(mask_path)
        plt.close()
        visualize_path[mask_name] = mask_path
    return visualize_path


def main():
    data_dir = constant_paths.get_data_dir_path()
    visualize_dir = constant_paths.get_logs_dir() / "visualize_labels"
    if visualize_dir.exists(): 
        rmtree(visualize_dir)
    visualize_dir.mkdir(parents=True)
    with Pool(12) as my_pool:
        func_args = []
        for i, mask_pkl in enumerate(data_dir.rglob("view_*_label_mask.pkl")):
            view_pkl = mask_pkl.parent / f"view_{mask_pkl.stem.split('_')[1]}.pkl"
            func_args.append((view_pkl, mask_pkl, visualize_dir, i, data_dir))
        visualize_paths = []
        for visualize_path in tqdm(my_pool.imap(visualize_pickle, func_args), total=len(func_args)):
            visualize_paths.append(visualize_path)

    visualize_helper(visualize_paths, visualize_dir)


if __name__ == "__main__":
    main()
