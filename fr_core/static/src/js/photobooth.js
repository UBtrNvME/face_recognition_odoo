odoo.define('fr_core.photobooth', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var Session = require('web.session');
    var QWeb = core.qweb;

    let Photobooth = AbstractAction.extend({
        className: "qzhub_action_photobooth_face_recognition",
        events: {
            'click .qzhub_start_process': '_onStartProcess',
            'click .qzhub_take_shot': '_onTakeAShot',
            'click .qzhub_finish_session': '_onFinishSession',
            'click .qzhub_btn_go_back': '_onGoBack'
        },

        init: function (parent, action, context) {
            this.Mode = ""
            this.action_manager = parent;
            this.VideoEvent = new Event('tryFaceRecAgain');
            this.StartVideo = new Event('startVideo')
            this.RepeatCounter = 0;
            this.Action = action;
            this._super.apply(this, arguments);
        },
        willStart: function () {
            let self = this;
            return this._super.apply(this, arguments).then(function () {
                if (self.Action.xml_id === "fr_core.face_recognition_create_face_model_action") {
                    self.Mode = "Create";
                } else {
                    self.Mode = "Recognise";
                }
                self.PartnerId = Session.partner_id;
            })
        },

        start: function () {
            var self = this;
            console.log(self)
            self.session = Session;
            console.log("Start")
            self.$el.html(QWeb.render("UserPhotoboothClientAction", {widget: self}));
            self.$(".qzhub_container").hide();
            self.$(".qzhub_welcome_to_face_create_box_bottom").hide();
            // Initializes media stream.
            window.addEventListener("startVideo", function () {
                self._startVideoStream()
            })
            if (self.Mode === "Recognise") {
                self.$(".qzhub_container").show();
                console.log("dispatch")
                window.dispatchEvent(self.StartVideo)
            }

        },

        _onStartProcess: function (event) {
            let self = this;
            console.log("On Start")
            window.dispatchEvent(self.StartVideo)
        },
        _onTakeAShot: function (event) {
            let self = this;
            self.$("#progress-bar").show()
            self.$("#progress-bar").css('width', '0%');
            let image = self._takeAPhoto();
            let url = `/api/v1/faceModel/${self.Action.context.active_id}/makeAttachment`;
            self.$(".qzhub_take_shot").hide();
            self.$(".qzhub_finish_session").hide();
            self._sendToController(url, image).then(function (result) {
                self.$("#progress-bar").css('width', '100%');
                self.$(".qzhub_take_shot").show();
                console.log(result)
                self.$(".qzhub_create_response_message_box").text("Ok, Now Take A New Angle");
                self.$(".qzhub_finish_session").show();
                self.$("#progress-bar").hide();
            });
        },

        _onGoBack: function (event) {
            window.history.back()

        },
        _onFinishSession: function (event) {
            let self = this;
            let mediaStream = self.VideoObj.srcObject;
            mediaStream.getTracks()[0].stop()
            // this.do_action({
            //     type: 'ir.actions.act_window',
            //     target: 'current',
            //     res_id: self.PartnerId,
            //     res_model: 'res.partner',
            //     views: [[false, 'form']],
            //     context: {},
            // });
            window.history.back()
        },

        _startVideoStream: function () {
            let self = this;
            self.$("#photobooth-container-with-all-things").show();
            self.$(".qzhub_welcome_to_face_create_box").hide();
            let stream = navigator.mediaDevices.getUserMedia({video: true})
                .then(function (mediaStream) {
                    let video = document.querySelector('#photobooth');
                    console.log(video)
                    let canvas = document.createElement("canvas");
                    video.srcObject = mediaStream;
                    self.VideoObj = video;
                    self.CanvasObj = canvas;

                    video.onloadedmetadata = function (e) {
                        console.log("Hello Bitch")
                        self.VideoObj.play();
                        if (self.Mode === "Recognise") {
                            console.log(self.Mode)
                            window.setTimeout(function () {
                                self.send_to_recognise()
                            }, 2000)

                        } else {
                            self.create_face_model()
                        }
                    };

                    video.addEventListener("tryFaceRecAgain", function () {
                        self.send_to_recognise()
                    })

                }).catch(function (err) {
                });
        },

        create_face_model: function () {
            let self = this;
            self.$(".qzhub_welcome_to_face_create_box_bottom").show();
            self.numberOfImagesTaken = 0;

            // if (response["status"] === 200) {
            //     numberOfImagesTaken += 1;
            //     self.$("qzhub_create_response_message_box").text("Ok, Now Take A New Angle" + "\n" + 10 - numberOfImagesTaken + " left");
            // }


        },
        _takeAPhoto: function () {
            let self = this;
            let canvas = self.CanvasObj;
            let video = self.VideoObj;
            canvas.height = video.offsetHeight;
            canvas.width = video.offsetWidth;
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            self.$("#progress-bar").css('width', '20%');
            return canvas.toDataURL("image/jpeg");
        },
        _sendToController: async function (apiPath, image) {
            const url = window.location.origin + apiPath;
            const data = {
                image_in_64encodeDataURL: image,
            };
            self.$("#progress-bar").css('width', '40%');
            const othePram = {
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
                method: "POST",
                mode: "cors",
                credentials: "same-origin"
            };
            return fetch(url, othePram)
                .then(data => {
                    console.log(data)
                    self.$("#progress-bar").css('width', '80%');
                    return data.json()
                })
                .then(res => {
                    // if (self.processControllerResponse(res["result"]['face_rec_result']) === false) {
                    //     window.location.href = "http://localhost:8060/web#id=3&action=119&model=res.partner&view_type=form&cids=1&menu_id=91"
                    // }
                    // return res.json();
                })
                .catch(error => console.log(error))
        },

        send_to_recognise: async function () {
            let self = this;
            console.log("Face found")
            let video = self.VideoObj;
            let mediaStream = video.srcObject;
            let image = self._takeAPhoto()
            // let base64ImageData = canvas.toDataURL("image/jpeg");

            const url = window.location.origin + `/api/v1/employee/${Session.uid}/processImage`;
            const data = {
                image_in_64encodeDataURL: image,
            };
            const othePram = {
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(data),
                method: "POST",
                mode: "cors",
                credentials: "same-origin"
            };
            console.log(data)
            return await fetch(url, othePram)
                .then(data => {
                    console.log(data)
                    return data.json()
                })
                .then(res => {
                    console.log('test', res)
                    if (self.processControllerResponse(res["result"]['face_rec_result']) === false) {
                        mediaStream.getTracks()[0].stop();
                        this.do_action({
                            type: 'ir.actions.act_window',
                            target: 'current',
                            res_id: self.PartnerId,
                            res_model: 'res.partner',
                            views: [[false, 'form']],
                            context: {},
                        });
                    }
                })
                .catch(error => console.log(error))

        },
        processControllerResponse: function (responseStatus) {
            let self = this;
            if (self.RepeatCounter > 50) {
                return false;
            }
            if (responseStatus === 200) {    /*Face Recognized*/
                self.VideoObj.srcObject.getTracks()[0].stop()
                console.log("Good Morning Boiiii!")
                this._rpc({
                    model: 'hr.employee',
                    method: 'attendance_manual',
                    args: [[self.Action.context.employee_id], 'hr_attendance.hr_attendance_action_my_attendances'],
                })
                    .then(function (result) {
                        if (result.action) {
                            self.do_action(result.action);
                        } else if (result.warning) {
                            self.do_warn(result.warning);
                        }
                    });
            } else if (responseStatus === 201) {    /*No Face Has Been Found On Image*/
                console.log("Sorry but I cant see face on the Image")
                self.VideoObj.dispatchEvent(self.VideoEvent)
                self.RepeatCounter += 1;
            } else if (responseStatus === 202) {    /*Too Many Faces Has Been Found On Image*/
                console.log("Too many faces has been found on the Image")
                self.VideoObj.dispatchEvent(self.VideoEvent)
                self.RepeatCounter += 1;
            } else if (responseStatus === 203) {    /*No Face Encodings*/
                console.log("Sorry But Employee Has No Face Encodings")
                console.log(self.PartnerId)
                self.VideoObj.srcObject.getTracks()[0].stop()
                this.do_action({
                    type: 'ir.actions.act_window',
                    target: 'current',
                    res_id: self.PartnerId,
                    res_model: 'res.partner',
                    views: [[false, 'form']],
                    context: {},
                });
            } else if (responseStatus === 204) {    /*Face Could Not Be Recognised Or This Is Other Employee*/
                console.log("Sorry but face on the Image is could not be recognised as Employee")
                self.RepeatCounter += 2;
                self.VideoObj.dispatchEvent(self.VideoEvent)
            } else {    /*Unknown Status Handler*/
                console.log("Unknown Error")
            }
        }
    });
    core.action_registry.add('fr_core.photobooth', Photobooth);

    return Photobooth;

});
