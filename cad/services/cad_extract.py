import json
import logging
from dataclasses import dataclass

import cv2
import pytesseract

from ..services import cad_helpers, img_manipulation

OBJECTS = None
CONNECTIONS = []
LINES = []

_logger = logging.getLogger(__name__)


@dataclass
class CadParseResult:
    objects: list
    lines: list
    text: dict


def extract(img_b64, data=None):
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

    image = img_manipulation.base64_to_ndarray(img_b64)
    gray_scale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray_scale = cv2.blur(gray_scale, (5, 5))
    gray_scale = cv2.fastNlMeansDenoising(gray_scale, None, 10, 10, 7)
    json_result = []
    for o in OBJECTS:
        object_name = o["name"]
        cad_objects, connections = cad_helpers.find_matching_objects(gray_scale, o)
        CONNECTIONS.extend(connections)
        for i, (x, y, w, h) in enumerate(cad_objects):
            json_result.append(
                {
                    "name": f"{object_name.lower().replace(' ', '_')}_{i + 1}",
                    "location": {"left": x, "top": y, "width": w, "height": h},
                    "symbol": object_name,
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

    TEXT = pytesseract.image_to_data(
        gray_scale, "rus+eng", output_type=pytesseract.Output.DICT
    )
    return CadParseResult(json_result, LINES, TEXT)


def serialize(db_data):
    res = []
    for rec in db_data:
        origin = json.loads(rec.origin)
        connections = json.loads(rec.connections)
        for connection in connections:
            x, y = connection["pos"]["x"], connection["pos"]["y"]
            connection["pos"] = {"x": x - origin[0], "y": y - origin[1]}
        jsonified = {
            "name": rec.name.title(),
            "template": rec.template.decode("utf-8"),
            "connections": connections,
            "thresh": rec.threshold,
            "size": {"width": rec.width, "height": rec.height},
            "mask": rec.mask.decode("utf-8") if rec.mask else None,
            "mirror": rec.mirror,
        }
        _logger.warning(jsonified)
        res.append(jsonified)
    return json.dumps(res)
