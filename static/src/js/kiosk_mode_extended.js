odoo.define('face_recognition.kiosk_mode_extended', function (require) {
    "use strict";

    let MyAttendances = require('hr_attendance.my_attendances')


    MyAttendances.include({
        update_attendance: function () {
            console.log("Hello")
            let self = this;
            this.do_action("face_recognition.face_recognition_photobooth_action", {
                additional_context: {
                    employee_id: self.employee.id,
                }
            });
        },

    });
});