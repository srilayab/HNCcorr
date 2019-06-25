"""Components for calcium-imaging movies in HNCcorr."""

import os
import numpy as np
from PIL import Image
from PIL.TiffTags import TAGS

from hnccorr.utils import (
    add_offset_to_coordinate,
    add_offset_set_coordinates,
    add_time_index,
    generate_pixels,
    list_images,
)


class Movie:
    """Calcium imaging movie class.

    Data is stored in an in-memory numpy array. Class supports both 2- and 3-
    dimensional movies.

    Attributes:
        name(str): Name of the experiment.
        _data (np.array): Fluorescence data. Array has size T x N1 x N2. T is
            the number of frame (num_frames), N1 and N2 are the number of
            pixels in the first and second dimension respectively.
        _data_size (tuple): Size of array _data.
    """

    def __init__(self, name, data):
        self.name = name
        self._data = data
        self.data_size = data.shape

    @classmethod
    def from_tiff_images(cls, name, image_dir, num_images, memmap=False):
        """Loads tiff images into a numpy array.

        Data is assumed to be stored in 16-bit unsigned integers. Frame numbers are
        assumed to be padded with zeros: 00000, 00001, 00002, etc. This is required
        such that Python sorts the images correctly. Frame numbers can start from 0, 1,
        or any other number. Files must have the extension ``.tiff``.

        If memmap is True, the data is not loaded into memory bot a memory mapped file
        on disk is used. The file is named ``$name.npy`` and is placed in the
        `image_dir` folder.

        Args:
            name (str): Movie name.
            image_dir (str): Path of image folder.
            num_images (int): Number of images in the folder.
            memmap (bool): If True, a memory-mapped file is used. (*Default: False*)

        Returns:
            Movie: Movie created from image files.
        """
        if memmap:
            data = cls._load_tiff_images_memmap(name, image_dir, num_images)
        else:
            data = cls._load_tiff_images_in_memory(image_dir, num_images)

        return cls(name, data)

    @staticmethod
    def _get_tiff_images_and_size(image_dir, num_images):
        """ Provides a sorted list of images and computes the required array size.

        Data is assumed to be stored in 16-bit unsigned integers. Frame numbers are
        assumed to be padded with zeros: 00000, 00001, 00002, etc. This is required
        such that Python sorts the images correctly. Frame numbers can start from 0, 1,
        or any other number. Files must have the extension ``.tiff``.

        Args:
            image_dir (str): Path of image folder.
            num_images (int): Number of images in the folder.

        Returns:
            tuple[List[Str], tuple]: Tuple of the list of images and the array size.
        """
        images = list_images(image_dir)

        assert len(images) == num_images

        # read image meta data
        first_image = images[0]
        with Image.open(first_image) as image:
            meta = {TAGS[key]: image.tag[key] for key in image.tag}

        # set size of data
        data_size = (len(images), meta["ImageLength"][0], meta["ImageWidth"][0])

        return images, data_size

    @classmethod
    def _load_tiff_images_in_memory(cls, image_dir, num_images):
        """Loads tiff images into an in-memory numpy array.

        Data is assumed to be stored in 16-bit unsigned integers. Frame numbers are
        assumed to be padded with zeros: 00000, 00001, 00002, etc. This is required
        such that Python sorts the images correctly. Frame numbers can start from 0, 1,
        or any other number. Files must have the extension ``.tiff``.

        Args:
            image_dir (str): Path of image folder.
            num_images (int): Number of images in the folder.

        Returns:
            np.array: Data with shape (T, N_1, N_2, N_3) where T is # of images.
        """
        images, data_size = cls._get_tiff_images_and_size(image_dir, num_images)

        data = np.zeros(data_size, np.uint16)

        cls._read_images(images, data)

        return data

    @staticmethod
    def _read_images(images, array):
        """ Loads images and copies them into the provided array.

        Args:
            images (list[Str]): Sorted list image paths.
            array (np.array like): T x N_1 x N_2 array-like object into which images
                should be loaded. T must equal the number of images in `images`. Each
                image should be of size N_1 x N_2.

        Returns:
            np.array like: The input array `array`.

        """
        for i, filename in enumerate(images):
            with Image.open(filename) as image:
                array[i, :, :] = np.array(image)

        return array

    @classmethod
    def _load_tiff_images_memmap(cls, name, image_dir, num_images):
        """Loads tiff images into a memory-mapped numpy array.

        The data is not loaded into memory bot a memory mapped file
        on disk is used. The file is named ``$name.npy`` and is placed in the
        `image_dir` folder.

        Data is assumed to be stored in 16-bit unsigned integers. Frame numbers are
        assumed to be padded with zeros: 00000, 00001, 00002, etc. This is required
        such that Python sorts the images correctly. Frame numbers can start from 0, 1,
        or any other number. Files must have the extension ``.tiff``.

        Args:
            name (str): Movie name.
            image_dir (str): Path of image folder.
            num_images (int): Number of images in the folder.

        Returns:
            np.memmap: Memory-mapped numpy array with movie data.
        """
        images, data_size = cls._get_tiff_images_and_size(image_dir, num_images)

        memmap_filename = os.path.join(image_dir, name + ".npy")
        memmap_array = np.memmap(
            memmap_filename, dtype=np.uint16, mode="w+", shape=data_size
        )

        cls._read_images(images, memmap_array)

        return memmap_array

    def __getitem__(self, key):
        """Provides direct access to the movie data.

        Movie is stored in array with shape (T, N_1, N_2, ...), where T is the number
        of frames in the movie. N_1, N_2, ... are the number of pixels in the first
        dimension, second dimension, etc.

        Args:
            key (tuple): Valid index for a numpy array.

        Returns:
            np.array
        """
        return self._data.__getitem__(key)

    def is_valid_pixel_coordinate(self, coordinate):
        """Checks if coordinate is a coordinate for a pixel in the movie."""
        if self.num_dimensions != len(coordinate):
            return False

        zero_tuple = (0,) * self.num_dimensions
        for i, lower, upper in zip(coordinate, zero_tuple, self.pixel_shape):
            if not lower <= i < upper:
                return False
        return True

    @property
    def num_frames(self):
        """Number of frames in the movie."""
        return self.data_size[0]

    @property
    def pixel_shape(self):
        """Resolution of the movie in pixels."""
        return self.data_size[1:]

    @property
    def num_pixels(self):
        """Number of pixels in the movie."""
        return np.product(self.data_size[1:])

    @property
    def num_dimensions(self):
        """Dimension of the movie (excludes time dimension)."""
        return len(self.data_size[1:])

    def extract_valid_pixels(self, pixels):
        """Returns subset of pixels that are valid coordinates for the movie."""
        return {pixel for pixel in pixels if self.is_valid_pixel_coordinate(pixel)}


class Patch:
    """Square subregion of Movie.

    Patch limits the data used for the segmentation of a potential cell. Given a center
    seed pixel, Patch defines a square subregion centered on the seed pixel with width
    patch_size. If the square extends outside the movie boundaries, then the subregion
    is shifted such that it stays within the movie boundaries.

    The patch also provides an alternative coordinate system with respect to the top
    left pixel of the patch. This pixel is the zero coordinate for the patch coordinate
    system. The coordinate offset is the coordinate of the top left pixel in the movie
    coordinate system.

    Attributes:
        _center_seed (tuple): Seed pixel that marks the potential cell. The pixel is
            represented as a tuple of coordinates. The coordinates are relative to the
            movie. The top left pixel of the movie represents zero.
        _coordinate_offset (tuple): Movie coordinates of the pixel that represents the
            zero coordinate in the Patch object. Similar to the Movie, pixels in the
            Patch are indexed from the top left corner.
        _data (np.array): Subset of the Movie data. Only data for the patch is stored.
        _movie (Movie): Movie for which the Patch object is a subregion.
        _num_dimensions (int): Dimension of the patch. It matches the dimension of the
            movie.
        _patch_size (int): length of the patch in each dimension. Must be an odd number.
    """

    def __init__(self, movie, center_seed, patch_size):
        """Initializes Patch object."""
        if patch_size % 2 == 0:
            raise ValueError("patch_size (%d) should be an odd number.")

        self._num_dimensions = movie.num_dimensions
        self._center_seed = center_seed
        self._patch_size = patch_size
        self._movie = movie
        self._coordinate_offset = self._compute_coordinate_offset()
        self._data = self._movie[self._movie_indices()]

    @property
    def num_frames(self):
        """Number of frames in the Movie."""
        return self._movie.num_frames

    @property
    def pixel_shape(self):
        """Shape of the patch in pixels. Does not not included the time dimension."""
        return (self._patch_size,) * self._num_dimensions

    def _compute_coordinate_offset(self):
        """Computes the coordinate offset of the patch.

        Confirms that the patch falls within the movie boundaries and shifts the patch
        if necessary. The center seed pixel may not be in the center of the patch if a
        shift is necessary.
        """
        half_width = int((self._patch_size - 1) / 2)

        topleft_coordinates = add_offset_to_coordinate(
            self._center_seed, (-half_width,) * self._num_dimensions
        )
        # shift left such that top left corner exists
        topleft_coordinates = list(max(x, 0) for x in topleft_coordinates)

        # bottomright corners (python-style index so not included)
        bottomright_coordinates = add_offset_to_coordinate(
            topleft_coordinates, (self._patch_size,) * self._num_dimensions
        )
        # shift right such that bottom right corner exists
        bottomright_coordinates = list(
            min(x, max_value)
            for x, max_value in zip(bottomright_coordinates, self._movie.pixel_shape)
        )

        topleft_coordinates = add_offset_to_coordinate(
            bottomright_coordinates, (-self._patch_size,) * self._num_dimensions
        )

        return topleft_coordinates

    def _movie_indices(self):
        """Computes the indices of the movie that correspond to the patch.

        For a patch with top left pixel (5, 5) and bottom right pixel (9, 9), this
        method returns ``(:, 5:10, 5:10)`` which can be used to acccess the data
        corresponding to the patch in the movie.
        """
        bottomright_coordinates = add_offset_to_coordinate(
            self._coordinate_offset, (self._patch_size,) * self._num_dimensions
        )

        # pixel indices
        idx = []
        for start, stop in zip(self._coordinate_offset, bottomright_coordinates):
            idx.append(slice(start, stop))
        return add_time_index(tuple(idx))

    def to_movie_coordinate(self, patch_coordinate):
        """Converts a movie coordinate into a patch coordinate.

        Args:
            patch_coordinate (tuple): Coordinates of a pixel in patch coordinate system.

        Returns:
            tuple: Coordinate of pixel in movie coordinate system.
        """
        return add_offset_to_coordinate(patch_coordinate, self._coordinate_offset)

    def to_patch_coordinate(self, movie_coordinate):
        """Converts a movie coordinate into a patch coordinate.

        Args:
            movie_coordinate (tuple): Coordinates of a pixel in movie coordinate system.

        Returns:
            tuple: Coordinate of pixel in patch coordinate system.
        """
        return add_offset_to_coordinate(
            movie_coordinate, [-x for x in self._coordinate_offset]
        )

    def enumerate_pixels(self):
        """Returns the movie coordinates of the pixels in the patch."""
        return add_offset_set_coordinates(
            generate_pixels(self.pixel_shape), self._coordinate_offset
        )

    def __getitem__(self, key):
        """Access data for pixels in the patch. Indexed in patch coordinates."""
        return self._data[key]
