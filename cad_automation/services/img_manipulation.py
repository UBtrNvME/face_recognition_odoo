"""
Python image manipulation helpers
=================================

This module provides set of helpers for image manipulation. That can dramatically
lessen work of the programmers which try to solve problems related to the Image Recognition,
Parsing, Analysis etc.

Example:


Todo:
    * Add other important functions for Image manipulation
"""
import base64

import cv2
import numpy as np


def base64_to_ndarray(im_b64):
    im_bytes = base64.b64decode(im_b64)
    im_arr = np.frombuffer(im_bytes, dtype=np.uint8)  # im_arr is one-dim Numpy array
    return cv2.imdecode(im_arr, flags=cv2.IMREAD_COLOR)


def ndarray_to_base64(ndarray):
    _, im_arr = cv2.imencode(".png", ndarray)
    im_bytes = im_arr.tobytes()
    return base64.b64encode(im_bytes)


def dataimage_to_base64(dataimage):
    start = dataimage.find(",")
    return dataimage[start + 1 :]


def binary_to_base64(bytes):
    # pylint: disable=redefined-builtin
    return base64.b64encode(bytes)


def base64_to_binary(im_b64):
    return base64.b64decode(im_b64)


def manipulation_helper(image, order, kwargs) -> np.ndarray:
    """Helper for Image Manipulation

    Helper which helps to apply Image Manipulation methods using their names,
    and keyword arguments.

    Args:
        image (np.ndarray): Image to apply filters on.
        order (str): Name of the function to apply on the iamge.
        kwargs (dict): Keyword arguments to pass on to the function.

    Returns:
        np.ndarray: Modified image.
    """
    function = getattr(ImageManipulation, order)
    return function(image, **kwargs)


class ImageManipulation(object):
    @staticmethod
    def deskew(image, max_skew: int = 10):
        """Deskew Image

        Finds degree of the skew of the image, then applies found degree of skew
        on the image and returns it.

        Args:
            image (np.ndarray): Image which has to be deskewed.
            max_skew (int, optional): Maximum skew to apply on the target image.

        Returns:
            np.ndarray: Image skewed in result of image processing.`

        """
        height, width, _ = image.shape

        # Create a grayscale image and denoise it
        im_gs = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        im_gs = cv2.fastNlMeansDenoising(im_gs, h=3)

        # Create an inverted B&W copy using Otsu (automatic) thresholding
        im_bw = cv2.threshold(im_gs, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        # Detect lines in this image. Parameters here mostly arrived at by trial and error.
        lines = cv2.HoughLinesP(
            im_bw, 1, np.pi / 180, 200, minLineLength=width / 12, maxLineGap=width / 150
        )

        # Collect the angles of these lines (in radians)
        angles = []
        for line in lines:
            angles.append(np.arctan2(line[0][3] - line[0][1], line[0][2] - line[0][0]))

        # If the majority of our lines are vertical, this is probably a landscape image
        landscape = (
            np.sum([abs(angle) > np.pi / 4 for angle in angles]) > len(angles) / 2
        )

        # Filter the angles to remove outliers based on max_skew
        if landscape:
            angles = [
                angle
                for angle in angles
                if np.deg2rad(90 - max_skew) < abs(angle) < np.deg2rad(90 + max_skew)
            ]
        else:
            angles = [angle for angle in angles if abs(angle) < np.deg2rad(max_skew)]

        if len(angles) < 5:
            # Insufficient data to deskew
            return image

        # Average the angles to a degree offset
        angle_deg = np.rad2deg(np.median(angles))

        # If this is landscape image, rotate the entire canvas appropriately
        if landscape:
            if angle_deg < 0:
                image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                angle_deg += 90
            elif angle_deg > 0:
                image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                angle_deg -= 90

        # Rotate the image by the residual offset
        rotation_matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle_deg, 1)

        return cv2.warpAffine(
            image, rotation_matrix, (width, height), borderMode=cv2.BORDER_REPLICATE
        )

    @staticmethod
    def change_color_format(image, **kwargs):
        return cv2.cvtColor(src=image, code=kwargs["code"])

    @staticmethod
    def threshold(image, **kwargs):
        return cv2.threshold(
            src=image,
            thresh=kwargs["thresh"],
            maxval=kwargs["maxval"],
            type=kwargs["type"],
        )[1]

    @staticmethod
    def rotate_bound(image, angle):
        # grab the dimensions of the image and then determine the
        # center
        (h, w) = image.shape[:2]
        (cX, cY) = (w / 2, h / 2)

        # grab the rotation matrix (applying the negative of the
        # angle to rotate clockwise), then grab the sine and cosine
        # (i.e., the rotation components of the matrix)
        M = cv2.getRotationMatrix2D((cX, cY), -angle, 1.0)
        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])

        # compute the new bounding dimensions of the image
        nW = int((h * sin) + (w * cos))
        nH = int((h * cos) + (w * sin))

        # adjust the rotation matrix to take into account translation
        M[0, 2] += (nW / 2) - cX
        M[1, 2] += (nH / 2) - cY

        # perform the actual rotation and return the image
        return cv2.warpAffine(image, M, (nW, nH)), cv2.invertAffineTransform(M)
