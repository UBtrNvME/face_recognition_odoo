import cv2
import face_recognition
import math


# CV2 cascades
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_smile.xml')


def compute_face_angle(face_landmarks):
    chin_characteristics = {
        'right_half_width': face_landmarks[0]['chin'][8][0] - face_landmarks[0]['chin'][0][0],
        'left_half_width' : face_landmarks[0]['chin'][16][0] - face_landmarks[0]['chin'][8][0],
        'total_width'     : face_landmarks[0]['chin'][16][0] - face_landmarks[0]['chin'][0][0]
    }
    angle = 45 - 180 * (chin_characteristics['left_half_width'] / chin_characteristics['total_width'] - 0.25)
    return angle


def get_smile_locations(gray):
    smiles = smile_cascade.detectMultiScale(gray, 1.3, 20)
    results = []
    for sx, sy, sw, sh in smiles:
        results.append((sx, sy, sw, sh))
    return results


def are_faces_smiling(frame, face_locations):
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    smile_locations = get_smile_locations(gray)
    result = {}
    for top, right, bottom, left in face_locations:
        x, y, w, h = left, top, right - left, bottom - top
        print(top, left, bottom, right)
        is_faces_smilling = False
        for sx, sy, sw, sh in smile_locations:
            print(x,"<", sx, "<", x + w,"\n", y,"<", sy, "<", y + h)
            if (x < sx < x + w) and (y < sy < y + h):
                is_faces_smilling = True
                break
        result[(x, y, w, h)] = is_faces_smilling
    return result
