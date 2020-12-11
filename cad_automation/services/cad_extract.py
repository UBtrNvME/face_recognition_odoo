import json
import logging

import cv2

from ..services import cad_helpers

OBJECTS = None
CONNECTIONS = []
LINES = []

_logger = logging.getLogger(__name__)


def main(img_b64, data=None):
    if data is None:
        _logger.warning(
            "Data parameter has not been parsed, trying to get data locally"
        )
        try:
            with open("./templates/objects1.json") as f:
                OBJECTS = json.load(f)
        except IOError:
            _logger.error("No objects.json in the current working directory.")
    else:
        _logger.info("Getting objects from the parsed data.")
        try:
            OBJECTS = json.loads(data)
        except json.JSONDecodeError:
            _logger.error("Problem getting json valid data from parsed parameter.")

    # image = img_manipulation.base64_to_ndarray(img_b64)
    gray_scale = cv2.cvtColor(img_b64, cv2.COLOR_BGR2GRAY)
    gray_scale = cv2.blur(gray_scale, (5, 5))
    gray_scale = cv2.fastNlMeansDenoising(gray_scale, None, 10, 10, 7)
    json_result = {"context": {"width": img_b64.shape[1], "height": img_b64.shape[0]}}
    for o in OBJECTS:
        object_name = o["name"]
        json_result[object_name] = []
        cad_objects, connections = cad_helpers.find_matching_objects(gray_scale, o)
        CONNECTIONS.extend(connections)
        for i, (x, y, w, h) in enumerate(cad_objects):
            json_result[object_name].append(
                {
                    "name": f"{object_name.lower().replace(' ', '_')}_{i + 1}",
                    "location": {"left": x, "top": y, "width": w, "height": h},
                }
            )

    for connect in CONNECTIONS:
        axis = 0 if connect[1][0] == 0 else 1
        line = cad_helpers.find_line(
            gray_scale,
            (20, 20),
            connect[0],
            axis,
            [connect[1][0] * 4, connect[1][1] * 4],
        )
        if line:
            LINES.append(line)

    return LINES, OBJECTS, TEXT
