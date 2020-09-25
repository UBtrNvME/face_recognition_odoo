import cv2
import os
import pytesseract
from PIL import Image
import tempfile
import re
import numpy as np
from io import BytesIO
from pebble import ProcessPool
from concurrent.futures import TimeoutError
from functools import partial
from imutils import rotate_bound

import logging

_logger = logging.getLogger(__name__)



def _import_document_characteristics(file_path):
    import json
    with open(file=file_path, mode='r') as f:
        return json.load(f)


def _set_image_dpi(image, from_file=False):
    if from_file:
        im = Image.open(image)
    else:
        im = Image.fromarray(image)
    length_x, width_y = im.size
    factor = min(1, float(1024.0 / length_x))
    size = int(factor * length_x), int(factor * width_y)
    im_resized = im.resize(size, Image.ANTIALIAS)
    temp_file = tempfile.NamedTemporaryFile(delete=False,   suffix='.png')
    temp_filename = temp_file.name
    im_resized.save(temp_filename, dpi=(300, 300))
    return temp_filename


def get_data_from_the_uid(frame, doc_char):
    data_json = doc_char['uid']['data']
    whole = {
        'width': frame.shape[1],
        'height': frame.shape[0]
    }
    original_dimensions = {
        'width': 85.72,
        'height': 54.03,
        'unit': 'mm'
    }
    res = {}
    for data in data_json:
        location = data['location']
        to_scan = frame.copy()
        if location == 'front':
            position = data['position']
            lang = data['lang']
            p = {key: (value/original_dimensions['height'])*whole['height'] if (key == 'y' or key == 'h') else (
                value/original_dimensions['width'])*whole['width'] for key, value in position.items()}
            name = data['name']
            # cv2.addText(frame, name, (int(
            #     p['x'])-10, int(p['y'])-10), "TimesNewRoman", color=(0, 0, 255))
            pt1 = (int(p['x']), int(p['y']))
            pt2 = (int(p['x']+p['w']), int(p['y']+p['h']))
            cv2.rectangle(frame, pt1, pt2, (255, 0, 0))
            to_scan = to_scan[pt1[1]:pt2[1], pt1[0]:pt2[0]]
            to_scan = cv2.cvtColor(to_scan, cv2.COLOR_BGR2GRAY)
            to_scan = cv2.blur(to_scan, (1, 1))
            to_scan = cv2.threshold(to_scan, 100, 200,
                                    cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            res[name] = pytesseract.image_to_string(
                to_scan, lang=lang, config='').strip()
    return res
def _rotate_image(image, angle):
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
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
    return cv2.warpAffine(image, M, (nW, nH))


def rotate_until_correct_orientation(image, doc_char):
    iin = re.compile(doc_char['uid']['characteristics']
                     ['front']['markers'][2]['regex'])
    kaz = re.compile(doc_char['uid']['characteristics']
                     ['front']['markers'][0]['regex'])
    rus = re.compile(doc_char['uid']['characteristics']
                     ['front']['markers'][1]['regex'])
    temp_image = None
    temp_diff = 1e9
    for i in range(0, 360, 1):
        image_copy = image.copy()
        image_copy = _rotate_image(image_copy, i)
        _logger.warning(i)
        data = pytesseract.image_to_data(
            image_copy,
            lang='kaz+eng',
            output_type=pytesseract.Output.DICT,
            # config='-c tessedit_char_whitelist=0123456789'
        )
        top_iin, top_kaz, top_rus = 0, 0, 0
        words = list(filter(iin.match, data['text']))

        if words:
            index = data['text'].index(words[0])
            top_iin = data['top'][index]
        else:
            continue

        words = list(filter(kaz.match, data['text']))
        if words:
            index = data['text'].index(words[0])
            top_kaz = data['top'][index]
        else:
            continue

        words = list(filter(rus.match, data['text']))
        if words:
            index = data['text'].index(words[0])
            top_rus = data['top'][index]
        else:
            continue

        if temp_diff >= abs(top_kaz - top_rus):
            temp_diff = abs(top_kaz - top_rus)
            temp_image = image_copy
            _logger.warning(temp_diff)
            if temp_diff <=2:
                break
    # cv2.imshow("WINDOW", temp_image)
    return temp_image

def rotate_until_correct_orientation_parallel(angle, image, doc_char):
    iin = re.compile(doc_char['uid']['characteristics']
                     ['front']['markers'][2]['regex'])
    kaz = re.compile(doc_char['uid']['characteristics']
                     ['front']['markers'][0]['regex'])
    rus = re.compile(doc_char['uid']['characteristics']
                     ['front']['markers'][1]['regex'])
    temp_image = None
    temp_diff = 1e9
    for i in range(angle, angle+1, 1):
        image_copy = image.copy()
        image_copy = rotate_bound(image_copy, i)
        print(i)
        data = pytesseract.image_to_data(
            image_copy,
            lang='kaz+eng',
            output_type=pytesseract.Output.DICT,
            # config='-c tessedit_char_whitelist=0123456789'
        )
        top_iin, top_kaz, top_rus = 0, 0, 0
        words = list(filter(iin.match, data['text']))
        if words:
            index = data['text'].index(words[0])
            top_iin = data['top'][index]
        else:
            continue

        words = list(filter(kaz.match, data['text']))
        if words:
            index = data['text'].index(words[0])
            top_kaz = data['top'][index]
        else:
            continue

        words = list(filter(rus.match, data['text']))
        if words:
            index = data['text'].index(words[0])
            top_rus = data['top'][index]
        else:
            continue

        if temp_diff >= abs(top_kaz - top_rus):
            temp_diff = abs(top_kaz - top_rus)
            temp_image = image_copy
            if temp_diff <=2:
                break
        print(temp_diff)
    return (temp_diff,temp_image)


def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype="float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    return rect


def four_point_transform(image, pts):
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped


def find_uid_markers(image, doc_char):
    image_copy = image.copy()

    data = pytesseract.image_to_data(
        image_copy, lang="kaz", output_type=pytesseract.Output.DICT,
        # config="-"
    )
    marker_datas = {}
    for marker in doc_char['uid']['characteristics']['front']['markers']:

        for i in range(len(data['text'])):
            if re.match(marker['regex'], data['text'][i].lower()):
                marker_datas[marker['name']] = {
                    'standard': marker['position'],
                    'on_image': {
                        'x': int(data['left'][i]),
                        'y': int(data['top'][i]),
                        'w': int(data['width'][i]),
                        'h': int(data['width'][i]*(marker['position']['h']/marker['position']['w']))
                    }
                }
    for key, value in marker_datas.items():
        if key == "top_right":
            value['on_image']['x'] = value['on_image']['x'] + \
                value['on_image']['w']
        if key == "bottom_left":
            value['on_image']['y'] = value['on_image']['y'] + \
                value['on_image']['h']
    return marker_datas


def find_uid_borders(image, doc_char, marker_datas):
    image_copy = image.copy()

    def _make_point(transformation_coeficient, x, y):
        new_x = x + transformation_coeficient['dx']
        new_y = y + transformation_coeficient['dy']
        return [int(new_x), int(new_y)]
    uid_standard_dimensions = doc_char['uid']['characteristics']['dimensions']
    image_dimensions = {
        'w': image_copy.shape[1],
        'h': image_copy.shape[0]
    }
    uid_points = []
    for key, value in marker_datas.items():
        transformation_parameter = tuple(key.split('_'))
        x_coef = (value['on_image']['w']/value['standard']['w'])
        y_coef = (value['on_image']['h']/value['standard']['h'])
        transformation_coeficient = {
            'dx': -value['standard']['x']*x_coef if transformation_parameter[1] == 'left' else (uid_standard_dimensions['width']-(value['standard']['x']+value['standard']['w']))*x_coef,
            'dy': -value['standard']['y']*y_coef if transformation_parameter[0] == 'top' else (uid_standard_dimensions['height']-(value['standard']['y']+value['standard']['h']))*y_coef
        }

        point = _make_point(
            transformation_coeficient,
            value['on_image']['x'],
            value['on_image']['y']
        )
        uid_points.append([point])
    uid_points.append([[
        uid_points[1][0][0] + (uid_points[2][0][0]-uid_points[0][0][0]),
        uid_points[1][0][1] + (uid_points[2][0][1]-uid_points[0][0][1])
    ]])
    return np.array(uid_points).reshape((4, 2))

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'document_characteristics.json')
def prepare_uid(iin_image, path_to_json=path):
    # prepare all required data and enhance dpi
    _logger.warning(path)
    doc_char = _import_document_characteristics(path_to_json)
    file_name = _set_image_dpi(iin_image)
    image = cv2.imread(file_name)
    os.remove(file_name)
    # rotate image until iin can be seen, because iin is the most difficult data to find
    # image = rotate_until_correct_orientation(image, doc_char)
    angles = [j if j >= 0 else 360 + j for i in range(0, 271, 90) for j in range(i - 8, i + 8 + 1)]
    _logger.warning(angles)
    # pool = Pool(processes=int(cpu_count()//3))
    # _logger.warning("cpu_count: %d" % (cpu_count()))
    # best_results = pool.map(partial(rotate_until_correct_orientation_parallel, image=image, doc_char=doc_char), angles)
    # pool.close()
    # pool.join()
    # _logger.warning(best_results)
    # best_results = sorted(best_results, key=lambda x: x[0])
    # image = best_results[0][1]
    # _logger.warning(image)
    results = []
    with ProcessPool(max_workers=4) as pool:
        future = pool.map(partial(rotate_until_correct_orientation_parallel, image=image, doc_char=doc_char), angles, timeout=20)
        iterator = future.result()
        while True:
            try:
                result = next(iterator)
                results.append(result)
            except StopIteration:
                break
            except TimeoutError as error:
                print("function took longer than %d seconds" % error.args[1])
                break

    markers = find_uid_markers(image, doc_char)
    points = find_uid_borders(image, doc_char, markers)
    ordered_points = order_points(points)
    image = four_point_transform(image, ordered_points)

    file_name = _set_image_dpi(image)
    image = cv2.imread(file_name)
    # image = cv2.cvtColor(image)
    os.remove(file_name)
    data = get_data_from_the_uid(image, doc_char)
    return data