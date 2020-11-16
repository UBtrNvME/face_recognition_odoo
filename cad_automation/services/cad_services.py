# -*- coding: utf-8 -*-
"""
cad_automation - Cad Automation Scripts
=======================================

Scripts for automated conversion of the pdf or other formats of the images
into lists of the lines and objects and output them. There will be 2 options for
outputing. First is to output as *.svg for each line
or object, and json which will contain location of those objects on
the original file. And second option is to outpus as lists of lines and segments.

Attributes:
    CV2_FILTERS (dict): All of the possible filter names, that can be used as an
    orders.

Todo:
    * Difficult shape detection and addition of them into workflow
"""

import timeit
from itertools import groupby
from typing import Iterator, List, Tuple

import cv2
import numpy as np
import pdf2image
from scipy import signal

from ..services.img_manipulation import (
    manipulation_helper,
)

# --------------------------------------------------------------------------------------
# CONSTANS
_LINE_WIDTH = 20
_BLACK = 0
_WHITE = 255
_MAX_FLOAT = 1.7976931348623157e308

HORIZONTAL_AXIS = 1
VERTICAL_AXIS = 0
CONNECTION_TEMPLATE = {
    "start": [],
    "end": [],
    "middle": [],
}
ARROW_LOCATION = (
    718,
    185,
    81,
    35,
)


# --------------------------------------------------------------------------------------
# WRAPPERS
def timer(function):
    def new_function(*args, **kwargs):
        start_time = timeit.default_timer()
        res = function(*args, **kwargs)
        elapsed = timeit.default_timer() - start_time
        print(
            'Function "{name}" took {time} seconds to complete.'.format(
                name=function.__name__, time=elapsed
            )
        )
        return res

    return new_function


# --------------------------------------------------------------------------------------
# EXCEPTIONS
class WrongObjectType(Exception):
    """Exception raised for errors when wrong object type is passed."""

    def __init__(self, possible_objects, message=("Wrong type of the object passed:")):
        self.possible_object_names = [obj.__name__ for obj in possible_objects]
        print(self)
        self.message = message + " possible objects are %s." % ", ".join(
            self.possible_object_names
        )
        super().__init__(self.message)


def butter_highpass(cutoff, frequency, order=5):
    """Butterworth highpass

    Design an Nth-order digital or analog Butterworth filter
    and return the filter coefficients.

    Args:
        cutoff (int): Cutoff.
        frequency (int): The sampling frequency of the digital system.
        order (int, optional): The order of the filter. Defaults to 5.

    Returns:
        b : Numerator (b) polynomial of the IIR filter.
        a : Denominator (a) polynomial of the IIR filter.
    """
    nyq = 0.5 * frequency
    normal_cutoff = cutoff / nyq
    return signal.butter(order, normal_cutoff, btype="high", analog=False)


def butter_highpass_filter(data, cutoff, frequency, order=5):
    """Application of the butter highpass filter on the data set

    Applies Butterworth filter with specified ``cutoff`` and ``frequency``
    on to ``data`` set and returns new data set with applied filter.
    Gets A and B coeficients from ``butter_highpass()`` and passess them into
    ``scipy.signal.filtfilt()``.

    Args:
        data (array-like): Data which needs to be filtered with highpass filter.
        cutoff (int): Cutoff.
        frequency (int): The sampling frequency of the digital system.
        order (int, optional): The order of the filter. Defaults to 5.

    Returns:
        array-like: Highpass filtered array-like object.
    """

    (b_coef, a_coef) = butter_highpass(cutoff, frequency, order=order)
    filtered_array = signal.filtfilt(b_coef, a_coef, data, padlen=16)
    return filtered_array


def find_peaks(data):
    """Peaks finding in data set.

    Find peaks in the data set which has been passed and then yields them.

    Args:
        data (array-like): Target array.

    Yields:
        m (int): Value of the peak.
        mi (int): Index of the peak.
    """
    start = 0
    sequence = []
    for key, group in groupby(data):
        sequence.append((key, start))
        start += sum(1 for _ in group)

    for (b, _), (m, mi), (a, _) in zip(
            sequence, sequence[1:], sequence[2:]
    ):  # pylint: disable=invalid-name
        if b < m and a < m:
            yield mi, m  # type (int, int) Index of the peak and value


def _get_original_index(index):
    """
    Returns original index of the line based on the index passed.

    Args:
        index (int): Index within unified list of lines.

    Returns:
        int: Index within original list.
    """
    return (index - (index % 2)) // 2


def _flood_search(matrix, pt, overal_direction, target_color):
    """
    Performs local flood searches around passed point and searches for color
    which has been specified. Search is performed within original matrix and in
    specific direction. After search is finished results are returned as minimatrix.

    Args:
        matrix (array-like): Original matrix of the Image object.
        pt (tuple): Point around which to perform search. Struct of the tuple is
        in (x,y) format.
        overal_direction (str): Overal direction of search.
        target_color (tuple): Color to search for in rgb format.

    Returns:
        list[list]: Mini matrix containing information about point surroundings.
    """
    len_orig_matrix = matrix.shape
    mini_matrix_size = 21
    mini_matrix = [[0] * mini_matrix_size] * mini_matrix_size
    x_virtual = (
        mini_matrix_size // 2
        if overal_direction in ["up", "down"]
        else 0
        if overal_direction == "right"
        else mini_matrix_size - 1
    )
    y_virtual = (
        mini_matrix_size // 2
        if overal_direction in ["left", "right"]
        else 0
        if overal_direction == "down"
        else mini_matrix_size - 1
    )
    diff_x = pt[0] - x_virtual
    diff_y = pt[1] - y_virtual

    for i in range(mini_matrix_size):
        for j in range(mini_matrix_size):
            if (
                    0 < j + diff_y < len_orig_matrix[0]
                    and 0 < i + diff_x < len_orig_matrix[1]
            ):

                mini_matrix[i][j] = (
                    1 if matrix[j + diff_y, i + diff_x] < target_color else 0
                )
            else:
                mini_matrix[i][j] = 0

    return mini_matrix


def _print_as_a_table(matrix):
    buf = "\n====" * len(matrix) + "=\n"
    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            buf += f"| {matrix[i][j]} "
        buf += "|\n" + "====" * len(matrix) + "=\n"
    return buf


def calculate_color_frequencies_by_axis(image, target_color=255, axis=0):
    """Calculates sums by axis of target color appearing in the image.

    Example:
        Array on the right will return          9 | 9 | 9 | 9
        following list [4,2,2,4] if             -------------
        target color will be equal to 9         9 | 9 | 0 | 9
        and axis will be chosen to be 0.        -------------
        Otherwise if axis is equal 1,           9 | 0 | 0 | 9
        then return array will be               -------------
        equal to [4,3,2,3].                     9 | 0 | 9 | 9

    Args:
        image (Optional(list, np.array)): Sample image.
        target_color (int, optional): Color which will be searched. Defaults to 255.
        axis (int, optional): The axis by which to sum. Defaults to 0.

    Returns:
        np.array: List of color frequencies by axis.
    """
    possible_types = (np.ndarray, np.matrix, list)
    if isinstance(image, possible_types):
        try:
            image = np.array(image)
        except Exception as conversion_error:
            raise NotImplementedError from conversion_error
    else:
        raise WrongObjectType(possible_types)

    assert 0 <= axis <= 1, "Argument axis should be in range 0-1"
    assert (
            isinstance(target_color, int) and 0 <= target_color <= 255
    ), "Argument target color has to be gray scale in range 0-255"

    return np.sum(image == target_color, axis=axis)


def read_bytes(datas):
    """Read bytes of the file and returns it as a numpy array.

    Args:
        bytes (Optional(bytes, str)): Bytes of the file object, for read.

    Returns:
        image (np.ndarray): Image converted into numpy array format.
    """
    image = None

    image = cv2.imdecode(datas, cv2.IMREAD_COLOR)

    # assert image != None, 'Decode has gone wrong'
    return image


def prepare_image_for_analysis(image_obj, mimetype, orders) -> np.ndarray:
    """Prepare image for further analysis.

    Converts bytes of the image into numpy array, then apply all of the commands
    required for future analysis.

    Args:
        image_obj (bytes): Bytes of the image or pdf which has to be analysed.
        mimetype (str): Mimetype of the image or pdf.
        orders (dict): Set of commands to be applied on the image,
            preprocessing commands.

    Returns:
        (np.ndarray): Preprocessed image, ready for further analysis.
    """
    if mimetype in ["PDF", ".pdf"]:
        image_obj = convert_pdf_to_img(image_obj)

    image = read_bytes(image_obj)
    image = apply_filters_on_image(image, orders)
    return image


def convert_pdf_to_img(pdf):
    """Converts pdf like byte array into image.

    Args:
        pdf (bytes): Bytes of pdf file

    Returns:
        [type]: Output buffer of image like object
    """
    buffer = pdf2image.convert_from_bytes(pdf, dpi=300)[0]
    return cv2.imencode(".jpg", buffer)


def apply_filters_on_image(image, orders: dict):
    """Applies stack of the order on the image from bottom to top.

    Args:
        image (np.ndarray): Image in the numpy array format,
            on which to apply filters.
        orders (list): List of the orders to execute on the image
            from botto, to top.

    Returns:
        image (np.ndarray): Image after all of the filters has been applied.
    """
    assert len(orders) > 0, "Orders buffer is empty"
    working_image = image.copy()
    for order, kwargs in orders.items():
        working_image = manipulation_helper(working_image, order=order, kwargs=kwargs)

    return working_image


def find_possible_lines_locations(image, pixel_frequencies, axis, **kwargs):
    kwargs = {
        "cutoff": 1,
        "frequency": 25,
        "order": 5,
    }
    kwargs.update(kwargs)
    noise_free_frequencies = butter_highpass_filter(
        data=pixel_frequencies,
        cutoff=kwargs["cutoff"],
        frequency=kwargs["frequency"],
        order=kwargs["order"],
    )
    peaks = list(find_peaks(noise_free_frequencies))
    for index, _ in peaks:
        line = [None, None]
        for i, color in axislinenumerate(image, axis, index):
            is_black_pixel = color != _WHITE
            if is_black_pixel and line[0] is None:
                line[0] = (index, i) if axis == 0 else (i, index)
            elif is_black_pixel:
                line[1] = (index, i) if axis == 0 else (i, index)
            elif not is_black_pixel and line[0] is not None and line[1] is not None:
                yield (axis, index), line
                line = [None, None]
            elif not is_black_pixel:
                continue


def axislinenumerate(ndarray: np.ndarray, axis: int, index: int) -> Tuple[int, int]:
    """Enumerate numpy array along one axis and one index.

    Example:
        Assuming that that we have numpy array::

            >>> array = numpy.array([[0,1,2,3], [0,1,2,3], [3,2,1,0]])

        If we would like to enumerate using our function we will get following result::

            >>> print(list(axislinenumerate(array, 0, 2)))
            [(0, 2), (1, 2), (2, 1)]

    Args:
        ndarray (np.ndarray): Numpy array which has to be enumerated.
        axis (int): Axis along which to enumerate numpy array.
        index (int): Index along which to enumerate numpy array.

    Yield:
        tuple(int, int): Tuple of the index and its value.
    """
    assert len(ndarray) > 0, "NDARRAY was not passed!"
    size = list(ndarray.shape)[:]
    if axis == 0:
        for i in range(size[axis]):
            yield i, ndarray[i, index]
    else:
        for i in range(size[axis]):
            yield i, ndarray[index, i]


def remove_duplicates(lines, dist):
    memo = {}
    for (axis, index), line in lines:
        is_duplicate = False
        for j in range(index - dist, index + dist):
            if j in memo:
                is_duplicate = True
                break

        if not is_duplicate:
            memo[index] = True
            yield (axis, index), line


@timer
def find_possible_objects(lines, line_characteristics, max_depth=7):
    def dfs(i, origin, depth, massive):
        if depth > max_depth:
            return []
        length = line_characteristics["length"][i]
        connections = line_characteristics["connections"][i]
        axis = line_characteristics["axis"][i]
        dist_from_origin = line_characteristics["dist_from_origin"][i]

        if i in massive and i != origin:
            return []

        if i == origin and 0 < depth <= 3:
            return []
        if i == origin and depth > 3:
            return [massive]

        massive.append(i)

        result = []

        for (line_index, intersection) in connections:
            if lines[line_index]:
                paths = dfs(line_index, origin, depth + 1, massive)
                if len(paths):
                    result.extend(paths)
        massive.pop()

        return result

    results = []

    for i, line in enumerate(lines):
        if line:
            res = dfs(i, i, 0, [])

            if len(res):
                results.extend(res)

    memo = []
    for arrays in results:
        sorted_array = sorted(arrays)
        if sorted_array not in memo:
            memo.append(sorted_array)
    return memo


def compute_length(line):
    return ((line[0][0] - line[1][0]) ** 2 + (line[0][1] - line[1][1]) ** 2) ** 0.5


def _get_line_coeficients(line):
    a = line[1][1] - line[0][1]
    b = line[0][0] - line[1][0]
    c = a * (line[0][0]) + b * (line[0][1])
    return a, b, c


def find_intersection(line1, line2):
    x, y = _MAX_FLOAT, _MAX_FLOAT

    # Line 1 characteristics

    (a1, b1, c1) = _get_line_coeficients(line1)

    # Line 2 characteristics

    (a2, b2, c2) = _get_line_coeficients(line2)

    determinant = a1 * b2 - a2 * b1

    if determinant != 0:
        x = (b2 * c1 - b1 * c2) / determinant
        y = (a1 * c2 - a2 * c1) / determinant

    # Else if determinant is equal 0 then we return max_floats

    return x, y


def define_line_connections(
        all_lines: List[Tuple[Tuple[int, int], List[Tuple[int, int]]]],
        line_index: int,
) -> Iterator[Tuple[int, Tuple[float, float]]]:
    """Defines connection of a line with an index `line_index` with lines from `all_lines`

    Yields connections of the line with other lines from all_lines list,
    where connection is described as index of connected line and point of intersection.

    Args:
        all_lines : List of all lines.
        line_index : Index of the line for which to find connections.
    """

    _, mline = all_lines[line_index]
    for i, (_, line) in enumerate(all_lines):
        intersection = find_intersection(mline, line)
        if intersection[0] == _MAX_FLOAT:
            continue
        yield i, intersection


def apply_rules_on_lines(rules=None, **kwargs):
    if "lines" not in kwargs and "inverted_line_characteristics" not in kwargs:
        return

    if rules is None:
        rules = {"length": ("gt", 20)}

    for rule, argument in rules.items():
        for value, indexes in kwargs["inverted_line_characteristics"][rule].items():
            # Applies rule operation (rule[0]) on
            # parameter values (key) and rule value (rule[1]),
            # if true skips, in other case marks out line indexes.
            # Example: if 'gt' a > b, if 'lt' a < b

            if not _operation_helper(argument[0], value, argument[1]):
                for i in indexes:
                    kwargs["lines"][i] = None


def _operation_helper(operator, a, b):
    result_state = {"gt": a > b, "ge": a >= b, "lt": a < b, "le": a <= b}
    return result_state[operator]


def invert_dict(adict: dict) -> dict:
    """

    Returns:
        dict:
    """
    reversed_dict = {}
    for key in adict:
        if key == "connections":
            continue
        reversed_dict[key] = {}
        for i, obj in enumerate(adict[key]):
            if obj not in reversed_dict[key]:
                reversed_dict[key][obj] = [i]
            else:
                reversed_dict[key][obj].append(i)
    return reversed_dict


def characterise_lines(lines):
    n = len(lines)  # pylint: disable=invalid-name
    mem = {
        "length": [None] * n,
        "axis": [None] * n,
        "dist_from_origin": [None] * n,
        "connections": [None] * n,
    }
    for i, ((faxis, findex), fline) in enumerate(lines):
        mem["length"][i] = compute_length(fline)
        mem["axis"][i] = faxis
        mem["dist_from_origin"][i] = findex
        mem["connections"][i] = list(define_line_connections(lines, i))

    return mem


def check_region_of_interest(roi, mask):
    mask = mask.copy()
    mask = cv2.resize(mask, roi.shape[::-1])
    result = np.bitwise_xor(roi, mask)
    non_zero_sum = np.sum(result != 0)
    return (
        non_zero_sum / (result.shape[0] * result.shape[1]) if non_zero_sum != 0 else 0
    )


def get_region_of_interest_from_segment(segments, lines):
    top, bottom, left, right = 1e15, 0, 1e15, 0
    for i in segments:
        for point in lines[i]:
            if point[0] > right:
                right = point[0]
            elif point[0] < left:
                left = point[0]
            if point[1] > bottom:
                point[1] = point[1]
            elif point[1] < top:
                top = point[1]
    return (top, left, right - left, bottom - top)


def main():
    orig_image = cv2.imread(
        "/home/aitemirkuandyk/Projects/my-scripts/pdf_to_dwg/graph.png"
    )
    _, bytes_image = cv2.imencode(".png", orig_image)
    commands = {
        "change_color_format": {"code": cv2.COLOR_BGR2GRAY},
        "threshold": {"thresh": 100, "maxval": 255, "type": cv2.THRESH_BINARY},
    }

    im = prepare_image_for_analysis(bytes_image, ".png", commands)

    sums_by_axis = {
        VERTICAL_AXIS: calculate_color_frequencies_by_axis(
            im, target_color=_BLACK, axis=VERTICAL_AXIS
        ),
        HORIZONTAL_AXIS: calculate_color_frequencies_by_axis(
            im, target_color=_BLACK, axis=HORIZONTAL_AXIS
        ),
    }
    lines = list(
        remove_duplicates(find_possible_lines_locations(im, sums_by_axis[0], 0), 2)
    )
    lines.extend(
        list(
            remove_duplicates(find_possible_lines_locations(im, sums_by_axis[1], 1), 2)
        )
    )
    line_characteristics = characterise_lines(lines)
    inverted_line_characteristics = invert_dict(line_characteristics)
    apply_rules_on_lines(
        **{
            "inverted_line_characteristics": inverted_line_characteristics,
            "lines": lines,
        }
    )
    possible_objects = find_possible_objects(lines, line_characteristics)
    print(sorted(possible_objects, key=len))


if __name__ == "__main__":
    main()
