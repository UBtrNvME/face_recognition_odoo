odoo.define('fr_core.kiosk_mode_extended', function (require) {
    "use strict";

    let MyAttendances = require('hr_attendance.my_attendances')


    MyAttendances.include({
        update_attendance: function () {
            console.log("Hello")
            let self = this;
            this.do_action("fr_core.face_recognition_photobooth_action", {
                additional_context: {
                    employee_id: self.employee.id,
                }
            });
        },

    });
});