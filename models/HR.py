# -*- coding: utf-8 -*-

from odoo import models, fields, api
import cv2, base64, io
from PIL import Image

class HR(models.Model):
    _inherit = 'hr.employee'

    attachment_ids = fields.Many2many('ir.attachment', 'face_recognition_hr_employee_ir_attachments_rel', 'employee_id',
                                      'attachment_id', string='Photos')

    def method_webcam_trigger(self):
        key = cv2.waitKey(1)
        webcam = cv2.VideoCapture(0)
        while True:
            try:
                print("4")
                check, frame = webcam.read()
                print(webcam.isOpened(), check, frame)
                if check:
                    cv2.imshow("Capturing", frame)
                    print("*********")
                    key = cv2.waitKey(1)
                    if key == ord('s'):
                        print("SAVE IMAGE")
                        cv2.imwrite(filename='product_image', img=frame)
                        img = Image.fromarray(frame, 'RGB')
                        img.save('my.jpg')
                        roiImg = img.crop()
                        imgByteArr = io.BytesIO()
                        roiImg.save(imgByteArr, format='JPG')
                        imgByteArr = imgByteArr.getvalue()
                        image_base64 = base64.b64encode(imgByteArr)
                        cv2.waitKey(1650)
                        cv2.destroyAllWindows()
                        vals = {
                            'image': image_base64,
                        }
                        self.write(vals)
                        break
                    elif key == ord('q'):
                        break
            except(KeyboardInterrupt):
                webcam.release()
                cv2.destroyAllWindows()
                break
        webcam.release()
        cv2.destroyAllWindows()

    def compare_with_image(self):
        return {
            'res_model': 'face.recognition',
            'type': 'ir.actions.act_window',
            'context': {
                "default_employee_id": self.id
            },
            'view_mode': 'form',
            # 'view_id': self.env.ref("face_recognition.face_recognition_compare_form").id,
            'target': 'new'
        }