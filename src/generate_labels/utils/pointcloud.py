"""
Original Source: https://github.com/kevinzakka/walle
Author: Kevin Zakka https://kzakka.com/

Abstraction for 3-D point clouds.
"""

from functools import reduce

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import random
import struct

def normalize_pc(pts):
    mean = np.mean(pts, axis=0)
    pts = pts - mean
    m = np.max(np.sqrt(np.sum(pts ** 2, axis=1)))
    pts = pts/m
    return pts.T

def sample_pointcloud_from_tsdf(tsdf, n_pt):
    size = np.array(tsdf.shape) // 2
    x, y, z = np.where(tsdf<=0)
    n_tot = len(x)
    pts = np.array(list(zip(x,y,z)))
    if n_tot == 0: # no point in the region, fill in (-1,-1,-1)?
        sampled_pts = np.zeros((n_pt, 3))-1
    elif len(pts) < n_pt: # no enough pt, , fill in (-1,-1,-1)?
        sampled_pts = np.concatenate([pts, np.zeros((n_pt-n_tot, 3))-1], axis=0)
    else:
        sampled_inds = random.sample(range(pts.shape[0]), n_pt)
        sampled_pts = pts[sampled_inds, :]
    sampled_pts -= size
    return normalize_pc(sampled_pts) # 3, np


class PointCloud:
    """A 3-D point cloud.
    """

    def __init__(self, *args):
        """Initializes the point cloud in any of the following ways:

        A.
            color_im (ndarray): An rgb image of shape (H, W, 3) or a
                grayscale image of shape (H, W).
            depth_im (ndarray): A depth image of shape (H, W). The
                depth values are expected to be in meters.
            intrinsics (ndarray): The camera intrinsics as a numpy
                array of shape (3, 3).
        B.
            xyzrgb (ndarray): A point cloud of shape (N, 3) if no color,
                (N, 4) if grayscale or (N, 6) if rgb.
        """
        self._point_cloud = np.zeros((0, 3))
        self._o3d_pc = o3d.geometry.PointCloud()
        self._is_normals_computed = False
        self._color_im = None
        self._depth_im = None
        self._height_map_color = None
        self._height_map_depth = None
        self._intr = None

        if len(args) == 1:
            point_cloud = args[0]
            self._check_valid_point_cloud(point_cloud)
            self._point_cloud = np.array(point_cloud, copy=True)
            self._is_color = self._point_cloud.shape[1] > 4
            self._preprocess_point_cloud()
            self._o3d_pc.points = o3d.utility.Vector3dVector(self._point_cloud[:, :3])
        elif len(args) == 3:
            color_im, depth_im, intrinsics = args
            self._check_valid_img(color_im, depth_im)
            self._check_valid_intr(intrinsics)
            self._color_im = np.array(color_im, copy=True)
            self._depth_im = np.array(depth_im, copy=True)
            self._intr = intrinsics
            if color_im.ndim == 3:
                self._is_color = True
                self._height, self._width, self._channels = color_im.shape
            else:
                self._is_color = False
                self._height, self._width = color_im.shape
            self._preprocess_img()
        else:
            raise ValueError("[!] Incorrect number of arguments.")

    def __repr__(self):
        s = "{}[{} points]"
        return s.format(self.__class__.__name__, len(self._point_cloud))

    def _check_valid_point_cloud(self, pc):
        """Checks that the input point cloud is valid.
        """
        assert pc.ndim == 2
        assert pc.shape[1] in [3, 4, 6]

    def _check_valid_img(self, img, depth):
        """Checks that the input data is valid.
        """
        color_cond = img.ndim == 3 and img.shape[-1] == 3
        gray_cond = img.ndim == 2
        depth_cond = img.shape[:2] == depth.shape
        assert (color_cond or gray_cond) and depth_cond

    def _check_valid_intr(self, intr):
        """Checks that the intrinsics are valid.
        """
        assert intr.shape == (3, 3)

    def _preprocess_img(self):
        """Pre-processes the color or gray image.
        """
        if self._color_im.max() > 1:
            self._color_im = (self._color_im / 255.0).astype("float32")

    def _preprocess_point_cloud(self):
        """Pre-processes the point cloud.
        """
        if self._point_cloud.shape[1] > 3:
            if self._point_cloud[:, 3:].max() > 1:
                self._point_cloud[:, 3:] /= 255

    @classmethod
    def from_point_cloud(cls, xyzrgb, intrinsics, im_shape, extrinsics=None):
        msg = "[!] Invalid image shape, product must equal point cloud length."
        assert len(xyzrgb) == np.prod(im_shape), msg
        color_im, depth_im = PointCloud.make_color_depth(xyzrgb, intrinsics, im_shape, extrinsics)
        inst = cls(color_im, depth_im, intrinsics)
        inst._point_cloud = xyzrgb
        inst._extr = extrinsics
        return inst

    def make_pointcloud(self, extrinsics=None, depth_trunc=3.0, trim=True):
        """Creates a 3-D point cloud.

        Args:
            extrinsics: (ndarray) The extrinsics of the camera
                of shape (4, 4).
            depth_trunc: (float) Depth values greater than this
                value are invalidated, i.e. set to NaN.
            trim: (bool) Whether to eliminate points with
                invalid depth values. This is useful for
                trimming the size of the point cloud.
        """
        extrinsics = np.eye(4) if extrinsics is None else extrinsics
        self._extr = extrinsics
        cc, rr = np.meshgrid(np.arange(self._width), np.arange(self._height), sparse=True)
        valid = (self._depth_im > 0) & (self._depth_im < depth_trunc)
        z = np.where(valid, self._depth_im, np.nan)
        x = np.where(valid, z * (cc - self._intr[0, 2]) / self._intr[0, 0], 0)
        y = np.where(valid, z * (rr - self._intr[1, 2]) / self._intr[1, 1], 0)
        if self._is_color:
            color = self._color_im.copy().transpose([2, 0, 1])
        else:
            color = [self._color_im.copy()]
        self._point_cloud = np.vstack([e.flatten() for e in [x, y, z, *color]]).T
        if not np.allclose(extrinsics, np.eye(4)):
            self._point_cloud = PointCloud.transform_point_cloud(self._point_cloud, extrinsics)
        if trim:
            self._point_cloud = self._point_cloud[~np.isnan(self._point_cloud[:, 2])]
        # store open3d version of pc
        pc = self._point_cloud[~np.isnan(self._point_cloud[:, 2])]
        pts = pc[:, :3].copy().astype(np.float64)
        if pc.shape[1] > 4:
            clrs = pc[:, 3:].copy().astype(np.float64)
        else:
            clrs = np.repeat((pc[:, 3:].copy()).astype(np.float64), 3, axis=1)
        self._o3d_pc.points = o3d.utility.Vector3dVector(pts)
        self._o3d_pc.colors = o3d.utility.Vector3dVector(clrs)

    def downsample(self, voxel_size=0.05, inplace=True):
        """Uniformly downsample the point cloud using voxel bucketization.
        """
        o3d_pc_down = self._o3d_pc.voxel_down_sample(voxel_size=voxel_size)
        pts_down = np.asarray(o3d_pc_down.points)
        clrs_down = np.asarray(o3d_pc_down.colors)
        pc_down = np.hstack([pts_down, clrs_down])
        print("downsample points: {:,}".format(len(pc_down)))
        if inplace:
            self._point_cloud = pc_down
            self._o3d_pc = o3d_pc_down
        else:
            ret = self.__class__(pc_down)
            ret._o3d_pc = o3d_pc_down
            ret._is_normals_computed = self._is_normals_computed
            return ret

    def compute_normals(self, radius=0.1, max_nn=30):
        """Estimate a normal for every point in the cloud.
        """
        self._o3d_pc.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=max_nn)
        )
        self._o3d_pc.orient_normals_to_align_with_direction()

    def make_heightmap(self, extrinsics, view_bounds, pixel_size, zero_level):
        """Returns a top-down orthographic heightmap image from the point cloud.

        Args:
            extrinsics: (ndarray) The extrinsics of the camera of shape (4, 4).
            view_bounds: (ndarray) The bounds of the heightmap region
                in 3D space in world coordinates of shape (3, 2).
                The rows are the [x, y, z] values and the columns
                are the respective [min, max] values.
            pixel_size: (float) A value defining the size of each pixel in meters,
                i.e. the heightmap resolution.
            zero_level: (float) A value defining the z-coordinate
                of the zero-level, i.e. the bottom of the heightmap.
        """
        if self._point_cloud is None:
            self.make_pointcloud(extrinsics)

        # compute heightmap spatial size
        heightmap_size = np.round(
            [
                (view_bounds[1, 1] - view_bounds[1, 0]) / pixel_size,
                (view_bounds[0, 1] - view_bounds[0, 0]) / pixel_size,
            ]
        ).astype(int)

        # figure out which indices are valid
        x_cond = np.logical_and(
            self._point_cloud[:, 0] >= view_bounds[0, 0],
            self._point_cloud[:, 0] < view_bounds[0, 1],
        )
        y_cond = np.logical_and(
            self._point_cloud[:, 1] >= view_bounds[1, 0],
            self._point_cloud[:, 1] < view_bounds[1, 1],
        )
        z_cond = np.logical_and(
            self._point_cloud[:, 2] >= view_bounds[2, 0],
            self._point_cloud[:, 2] < view_bounds[2, 1],
        )
        heightmap_valid_ind = reduce(np.logical_and, [x_cond, y_cond, z_cond])

        # remove invalid indices
        point_cloud_valid = self._point_cloud[heightmap_valid_ind]
        if point_cloud_valid.shape[0] == 0:
            print("[!] View bounds are too restrictive.")
        points = point_cloud_valid[:, :3]
        color = point_cloud_valid[:, 3:]

        # sort points by z value
        sort_z_ind = np.argsort(points[:, 2])
        points_sorted = points[sort_z_ind]
        color_sorted = color[sort_z_ind]

        # backproject pointcloud onto heightmap
        heightmap_pixel_x = np.round((points_sorted[:, 0] - view_bounds[0, 0]) / pixel_size).astype(
            int
        )
        heightmap_pixel_y = np.round((points_sorted[:, 1] - view_bounds[1, 0]) / pixel_size).astype(
            int
        )

        # clip to ensure within image bounds
        heightmap_pixel_x = np.clip(heightmap_pixel_x, 0, heightmap_size[1] - 1)
        heightmap_pixel_y = np.clip(heightmap_pixel_y, 0, heightmap_size[0] - 1)

        # get height values from z values minus zero level
        self._height_map_depth = np.zeros(heightmap_size)
        self._height_map_depth[heightmap_pixel_y, heightmap_pixel_x] = points_sorted[:, 2]
        self._height_map_depth = self._height_map_depth - zero_level
        self._height_map_depth[self._height_map_depth < 0] = 0
        self._height_map_depth[self._height_map_depth == -zero_level] = 0

        # finally map the colors
        num_channels = 3 if self._is_color else 1
        self._height_map_color = np.zeros(
            (heightmap_size[0], heightmap_size[1], num_channels), dtype="uint8"
        )
        self._height_map_color[heightmap_pixel_y, heightmap_pixel_x] = color_sorted * 255
        self._height_map_color = self._height_map_color.squeeze()

    @staticmethod
    def transform_point_cloud(point_cloud, transforms):
        """Applies a rigid transform to a point cloud.

        Args:
            point_cloud: (ndarray) The point cloud of shape (N, 6) or (N, 4) or (N, 3).
            transform: (ndarray) The rigid transform of shape (4, 4). Can also
                be a list of transforms to apply sequentially.

        Returns:
            point_cloud_T: (ndarray) The transformed point cloud.
        """
        num_pts = point_cloud.shape[0]
        pts = point_cloud[:, :3]
        pts_h = np.hstack([pts, np.ones((num_pts, 1))])
        if not isinstance(transforms, (list, tuple)):
            transforms = [transforms]
        for transform in transforms:
            pts_t = (transform @ pts_h.T).T
        if point_cloud.shape[1] > 3:
            clrs = point_cloud[:, 3:]
            point_cloud = np.hstack([pts_t[:, :3], clrs])
            return point_cloud
        return pts_t[:, :3]


    def transform_point_cloud2(self, trans_mat):
        self._o3d_pc = self._o3d_pc.transform(trans_mat)

    @staticmethod
    def points2pixels(points, intr, extr=None):
        """Projects 3-D points into 2D pixels.

        Args:
            points: (ndarray) The xyz points of shape (N, 3).
            intr: (ndarray) The camera intrinsics of shape (3, 3).
            extr: (ndarray) The camera extrinsics of shape (4, 4).

        Returns:
            uv: (ndarray) The uv pixels of shape (N, 2).
        """
        extr = np.eye(4) if extr is None else extr
        cx, cy = intr[0, 2], intr[1, 2]
        fx, fy = intr[0, 0], intr[1, 1]
        points = PointCloud.transform_point_cloud(points, np.linalg.inv(extr))
        x = points[:, 0]
        y = points[:, 1]
        z = points[:, 2]
        v = np.round((x * fx / z) + cx).astype("int")
        u = np.round((y * fy / z) + cy).astype("int")
        uv = np.vstack([u, v]).T
        return uv

    @staticmethod
    def make_color_depth(xyzrgb, intrinsics, im_shape, extrinsics):
        """Creates a color and depth image from a 3-D point cloud.
        """
        depth_im = np.zeros(im_shape)
        color_im = np.zeros((*im_shape, 3))
        pts = xyzrgb[:, :3]
        clrs = xyzrgb[:, 3:]
        uv = PointCloud.points2pixels(pts, intrinsics, extrinsics)
        valid_idx = (
            (uv[:, 0] >= 0) & (uv[:, 0] < im_shape[0]) & (uv[:, 1] >= 0) & (uv[:, 1] < im_shape[1])
        )
        uv = uv[valid_idx]
        clrs = clrs[valid_idx]
        depth = pts[valid_idx, 2]
        depth_im[uv[:, 0], uv[:, 1]] = depth
        color_im[uv[:, 0], uv[:, 1]] = clrs
        return color_im, depth_im

    def view_point_cloud(self, frame=True):
        """Draws the point cloud in Open3D.

        Args:
            frame: (bool) Whether to plot the xyz coordinate frame.
        """
        pcs = [self._o3d_pc]
        # o3d_pc[0].transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])
        if frame:
            pcs.append(
                o3d.geometry.TriangleMesh.create_coordinate_frame(size=0.1, origin=[0, 0, 0])
            )
        o3d.visualization.draw_geometries(pcs)

    def view_imgs(self, figsize=None):
        """Displays the color and depth images side by side.
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        axes[0].imshow(self._color_im, cmap=None if self._is_color else "gray")
        axes[1].imshow(self._depth_im)
        for ax in axes:
            ax.axis("off")
        plt.show()

    def view_height_map(self, figsize=None):
        """Displays the color and depth height maps side by side.
        """
        fig, axes = plt.subplots(1, 2, figsize=figsize)
        axes[0].imshow(self._height_map_color, cmap=None if self._is_color else "gray")
        axes[1].imshow(self._height_map_depth)
        for ax in axes:
            ax.axis("off")
        plt.show()

    @property
    def point_cloud(self):
        if self._point_cloud is None:
            self.make_pointcloud()
        return self._point_cloud

    @property
    def normals(self):
        return np.asarray(self._o3d_pc.normals)

    @property
    def color_im(self):
        return self._color_im

    @property
    def depth_im(self):
        return self._depth_im

    @property
    def height_map_color(self):
        if self._height_map_color is None:
            raise AttributeError("[!] You must first create the heightmap.")
        return self._height_map_color

    @property
    def height_map_depth(self):
        if self._height_map_depth is None:
            raise AttributeError("[!] You must first create the heightmap.")
        return self._height_map_depth

    @property
    def shape(self):
        if self._point_cloud is None:
            raise ValueError("[!] You must first create the point cloud.")
        return self._point_cloud.shape

    @property
    def o3d_pc(self):
        return self._o3d_pc

    def export(self, path):
        o3d.io.write_point_cloud(str(path), self._o3d_pc, write_ascii=True)
    
def viz_normals(pts, clrs, normals):
    # Source: https://github.com/kevinzakka/learn-ransac/blob/master/normals.py#L125
    pts = pts.copy().astype(np.float64)
    clrs = clrs.copy().astype(np.float64)
    normals = normals.copy().astype(np.float64)
    o3d_pc = [o3d.geometry.PointCloud()]
    o3d_pc[0].points = o3d.utility.Vector3dVector(pts)
    o3d_pc[0].colors = o3d.utility.Vector3dVector(clrs)
    o3d_pc[0].normals = o3d.utility.Vector3dVector(normals)
    o3d_pc.append(o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=0.1, origin=[0, 0, 0]))
    o3d.visualization.draw_geometries(o3d_pc)

def get_pointcloud_color(color_image,depth_image,camera_intrinsics):
    """ creates 3D point cloud of rgb images by taking depth information
        input : color image: numpy array[h,w,c], dtype= uint8
                depth image: numpy array[h,w] values of all channels will be same
        output : camera_points, color_points - both of shape(no. of pixels, 3)
    """

    image_height = depth_image.shape[0]
    image_width = depth_image.shape[1]
    pixel_x,pixel_y = np.meshgrid(np.linspace(0,image_width-1,image_width),
                                  np.linspace(0,image_height-1,image_height))
    camera_points_x = np.multiply(pixel_x-camera_intrinsics[0,2],depth_image/camera_intrinsics[0,0])
    camera_points_y = np.multiply(pixel_y-camera_intrinsics[1,2],depth_image/camera_intrinsics[1,1])
    camera_points_z = depth_image
    camera_points = np.array([camera_points_x,camera_points_y,camera_points_z]).transpose(1,2,0).reshape(-1,3)

    color_points = color_image.reshape(-1,3)

    # Remove invalid 3D points (where depth == 0)
    valid_depth_ind = np.where(depth_image.flatten() > 0)[0]
    camera_points = camera_points[valid_depth_ind,:]
    color_points = color_points[valid_depth_ind,:]

    return camera_points,color_points

def write_pointcloud(filename,xyz_points,rgb_points=None):

    """ creates a .pkl file of the point clouds generated
    """

    assert xyz_points.shape[1] == 3,'Input XYZ points should be Nx3 float array'
    if rgb_points is None:
        rgb_points = np.ones(xyz_points.shape).astype(np.uint8)*255
    assert xyz_points.shape == rgb_points.shape,'Input RGB colors should be Nx3 float array and have same size as input XYZ points'

    # Write header of .ply file
    fid = open(filename,'wb')
    fid.write(bytes('ply\n', 'utf-8'))
    fid.write(bytes('format binary_little_endian 1.0\n', 'utf-8'))
    fid.write(bytes('element vertex %d\n'%xyz_points.shape[0], 'utf-8'))
    fid.write(bytes('property float x\n', 'utf-8'))
    fid.write(bytes('property float y\n', 'utf-8'))
    fid.write(bytes('property float z\n', 'utf-8'))
    fid.write(bytes('property uchar red\n', 'utf-8'))
    fid.write(bytes('property uchar green\n', 'utf-8'))
    fid.write(bytes('property uchar blue\n', 'utf-8'))
    fid.write(bytes('end_header\n', 'utf-8'))

    # Write 3D points to .ply file
    for i in range(xyz_points.shape[0]):
        fid.write(bytearray(struct.pack("fffccc",xyz_points[i,0],xyz_points[i,1],xyz_points[i,2],
                                        rgb_points[i,0].tobytes(),rgb_points[i,1].tobytes(),
                                        rgb_points[i,2].tobytes())))
    fid.close()