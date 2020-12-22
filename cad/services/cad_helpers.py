import sys

import cv2
import imutils
import numpy as np

from ..services.img_manipulation import ImageManipulation as IM, base64_to_ndarray

GREEN = (0, 255, 0)


def template_matching(image, template, thresh, mask=None):
    w, h = template.shape[::-1]
    if mask is not None:
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED, mask=mask)
    else:
        res = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)

    loc = np.where(res >= thresh)
    for pt in zip(*loc[::-1]):
        yield pt[0], pt[1], w, h


def _mirror_template_if_needed(templates, value):
    if value == "":
        return
    a_map = {"vertical": 0, "horizontal": 1}
    templates.append(cv2.flip(templates[0], a_map[value]))


def find_matching_objects(orig_image, cad_object):
    objects = []
    object_connections = []
    templates = []
    if "template" in cad_object:
        templates.append(
            cv2.cvtColor(base64_to_ndarray(cad_object["template"]), cv2.COLOR_BGR2GRAY)
        )
    else:
        templates.append(cv2.imread(cad_object["path"], 0))

    if "mirror" in cad_object:
        _mirror_template_if_needed(templates, cad_object["mirror"])

    mask = None
    if "mask" in cad_object:
        mask = cv2.cvtColor(base64_to_ndarray(cad_object["mask"]), cv2.COLOR_BGR2GRAY)

    for angle in range(0, 360, 90):
        image, inverse_matrix = IM.rotate_bound(orig_image, angle)
        for template in templates:
            for x, y, w, h in template_matching(
                image, template, cad_object["thresh"], mask=mask
            ):
                if np.sum(image[y : y + h, x : x + w] == 0) < 30:
                    continue

                rect = find_location_on_original_image((x, y, w, h), inverse_matrix)
                connections = _locate_connections_on_image(
                    rect, inverse_matrix, cad_object["connections"]
                )
                objects.append(rect)
                object_connections.extend(connections)
                cut_from(image, roi=(x, y, w, h), mask=mask)
        orig_image, _ = IM.rotate_bound(image, -angle)
    return objects, object_connections


def _int(*args):
    return [int(arg) for arg in args]


def _locate_connections_on_image(rect, matrix, connections):
    center_point = _int(*_compute_center_point(rect))
    result = []
    for connection in connections:
        position_vector = _vector_transform(connection["pos"], matrix, flags="-T-D")
        direction_vector = _vector_transform(connection["dir"], matrix, flags="-T-D")
        result.append((np.add(center_point, position_vector), direction_vector))
    return np.array(result, dtype=int)


def cut_from(image, *, roi, mask=None):
    (x, y, w, h) = roi
    if mask is None:
        mask = np.full((w, h), 255)
    image[y : y + h, x : x + w] = cv2.bitwise_and(image[y : y + h, x : x + w], mask)


def _convert_from_dict(dictionary):
    return [item for item in dictionary.values()]


def _vector_transform(vector, matrix, *, flags=""):
    if "-T" in flags:
        matrix[0][2] = matrix[1][2] = 0
    if "-D" in flags:
        vector = _convert_from_dict(vector)
    return cv2.transform(np.array([[vector]]), matrix)[0][0]


def _compute_center_point(rectangle):
    points = rectangle
    if type(rectangle) != type(list):
        points = _get_points(rectangle)
    return [sum(x) / 4 for x in zip(*points)]


def downscale(img, scale_percent):
    # percent of original size
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    # resize image
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    return resized


def _apply_inverse_matrix_on_rectangle(rect, inverse_matrix):
    for point in _get_points(rect):
        yield _vector_transform(point, inverse_matrix)


def _make_rectangle(points):
    points.sort(key=sum)
    [x, y] = points[0]
    [w, h] = np.subtract(points[3], points[0])
    return x, y, w, h


def find_location_on_original_image(rect, inverse_matrix):
    points = list(_apply_inverse_matrix_on_rectangle(rect, inverse_matrix))
    rect = _make_rectangle(points)
    return rect


def _get_points(rect):
    x, y, w, h = rect
    return [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]


def pyramid(image, scale=1.5, minSize=(30, 30)):
    # yield the original image
    yield image
    # keep looping over the pyramid
    while True:
        # compute the new dimensions of the image and resize it
        w = int(image.shape[1] / scale)
        image = imutils.resize(image, width=w)
        # if the resized image does not meet the supplied minimum
        # size, then stop constructing the pyramid
        if image.shape[0] < minSize[1] or image.shape[1] < minSize[0]:
            break
        # yield the next image in the pyramid
        yield image


def sliding_window(array, window, step_size):
    x_orientation = np.array([0, array.shape[1]])
    y_orientation = np.array([0, array.shape[0]])
    y_is_reverse = False
    x_is_reverse = False
    if step_size[0] == 0:
        step_size[0] = 1
    if step_size[1] == 0:
        step_size[1] = 1
    if step_size[0] < 0:
        x_orientation = np.flip(x_orientation - 1)
        x_is_reverse = True

    if step_size[1] < 0:
        y_orientation = np.flip(y_orientation - 1)
        y_is_reverse = True

    for y in range(y_orientation[0], y_orientation[1], step_size[1]):
        y1 = y - window[1] * (y_is_reverse)
        y2 = y + window[1] * (-y_is_reverse + 1)

        if y2 > array.shape[0] or y1 < 0:
            break
        for x in range(x_orientation[0], x_orientation[1], step_size[0]):
            x1 = x - window[0] * (x_is_reverse)
            x2 = x + window[0] * (-x_is_reverse + 1)
            if x2 > array.shape[1] or x1 < 0:
                break

            yield x, y, array[y1:y2, x1:x2]


def _designate_roi(image, window_size, origin, axis, step_size):
    x, y, w, h = origin[0], origin[1], window_size[0], window_size[1]
    if axis == 1:
        if step_size[0] < 0:
            w = x - 0
            x -= w
        else:
            w = image.shape[1] - x
    else:
        if step_size[1] < 0:
            h = y - 0
            y -= h
        else:
            h = image.shape[0] - y
    return x, y, image[y : y + h, x : x + w]


def find_line(image, window_size, connection_point, axis, step_size):
    origin = _generate_window_origin(connection_point, window_size, axis)
    line = [None, None]
    difference_x, difference_y, roi = _designate_roi(
        image, window_size, origin, axis, step_size
    )
    for window in sliding_window(roi, window_size, step_size):
        if np.sum(window[2] == 0) > 10:
            if line[0] is None:
                line[0] = [window[0] + difference_x, window[1] + difference_y]
            else:
                line[1] = [window[0] + difference_x, window[1] + difference_y]
        else:
            break
    if line[1] is not None:
        if axis == 1:
            line[1][0] += -window_size[0] if step_size[0] < 0 else window_size[0]
        else:
            line[1][1] += -window_size[1] if step_size[1] < 0 else window_size[1]
        pt2 = line[1].copy()
        pt2[axis] += window_size[axis]
        cv2.rectangle(image, tuple(line[0]), tuple(pt2), 255, -1)
    return line if line[0] and line[1] else None


def _generate_window_origin(connection_point, window_size, axis):
    connection_point[axis] -= window_size[axis] // 2
    return connection_point


def _render_mask_with_points(mask, points):

    number_of_points = len(points)
    for point in points:
        cv2.circle(mask, center=tuple(point), radius=2, thickness=-1, color=GREEN)

    if number_of_points > 1:
        for i in range(1, number_of_points):
            cv2.line(
                mask,
                pt1=tuple(points[i - 1]),
                pt2=tuple(points[i]),
                color=GREEN,
                thickness=1,
            )
    if number_of_points > 2:
        cv2.line(
            mask, pt1=tuple(points[-1]), pt2=tuple(points[0]), color=GREEN, thickness=1
        )
    return mask


def calculate_threshold(test_image, template, template_mask):
    test_image = base64_to_ndarray(test_image)
    template = base64_to_ndarray(template)
    template_mask = base64_to_ndarray(template_mask)
    res = cv2.matchTemplate(
        test_image, template, cv2.TM_CCOEFF_NORMED, mask=template_mask,
    )
    return res
