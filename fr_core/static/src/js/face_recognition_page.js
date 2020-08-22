odoo.define('fr_core.face_recognise_sign_up', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');

    publicWidget.registry.SignUpFaceRecognition = publicWidget.Widget.extend({
        selector: '.qzhub_signup_form_face_recognition',
        events: {
            'submit': '_onSubmit',
        },

        start: function () {
            let self = this;
            self.Data = {};
            self.Events = {}
            self.Events.TryAgain = new Event('tryAgain');
            console.log('face_recognition_page.js')
            console.log(self)
            let stream = navigator.mediaDevices.getUserMedia({video: true})
                .then(function (mediaStream) {
                    let video = document.querySelector('#photobooth');
                    let canvas = document.createElement("canvas");
                    video.srcObject = mediaStream;
                    self.Data.video = video;
                    self.Data.canvas = canvas;
                    self.Data.video.onloadedmetadata = function (e) {
                        self.Data.video.play();
                        self.process_video()
                    };
                    window.addEventListener('tryAgain', function (e) {
                        console.log("Event_dispatch")
                        self.process_video()
                    })
                }).catch(function (err) {
                });


        },

        process_video: function () {
            console.log("Hello from process_video")
            let self = this;
            self.$("#progress-bar").show();
            let image = self._takeAPhoto();
            self.$("#progress-bar").css('width', '40%');
            self.send_image_to_controller(image);
            self.$("#progress-bar").css('width', '80%');
        },

        send_image_to_controller: function (image) {
            console.log(window.location.pathname, window.location.pathname.includes('signup'))
            if (window.location.pathname.includes('signup')) {
                let self = this;
                console.log('send request')
                this._rpc({
                    route: '/api/v1/processUinImage',
                    params: {
                        'unknown_uin': image,
                        'face_model_id': window.location.pathname.split('/').pop()
                    }
                }).then(result => {
                    if (result.length === 1) {
                        window.location.href = `${window.location.origin}/`
                    } else {
                        let tryAgain = window.confirm("Sorry, could not recognize your uin, try again.")
                        self._tryAgain(tryAgain)
                    }
                })
            } else {
                let self = this;
                console.log('make request')
                this._rpc({
                    route: '/api/v1/processImage',
                    params: {
                        'unknown_user_image': image,
                    },
                }).then(function (result) {
                    console.log('result', result);
                    self.$("#progress-bar").css('width', '100%');
                    if (result.length > 1) {
                        window.location.href = `${window.location.origin}/web/login?isRecognised=${true}&login=${result[0]}&hasPassword=${result[1]}&name=${result[2]}`
                    } else {
                        if (result === false) {
                            self._tryAgain(true)
                        }
                        else if (result[0] === "TooManyFaces") { // Too Many Faces
                            let tryAgain = window.confirm("Sorry, more than one face in the frame, try again.")
                            self._tryAgain(tryAgain)
                        } else if (result[0] === "NoFace") {
                            let tryAgain = window.confirm("Sorry, camera didn't detect any face, try again.")
                            self._tryAgain(tryAgain)
                        } else {
                            window.location.href = `${window.location.origin}/web/login?isRecognised=${false}&model=${result[0]}`
                        }

                    }
                }).catch(function (error) {
                    console.log('request error', error)
                });
            }
        },

        _takeAPhoto: function () {
            let self = this;
            let canvas = self.Data.canvas;
            let video = self.Data.video;
            canvas.height = video.offsetHeight;
            canvas.width = video.offsetWidth;
            canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
            return canvas.toDataURL("image/jpeg");
        },

        _tryAgain: function (condition) {
            let self = this

            self.$("#progress-bar").css('width', '20%');
            self.$("#progress-bar").hide();
            if (condition) {
                window.setTimeout(function () {
                    window.dispatchEvent(self.Events.TryAgain)
                }, 1000)

            } else {
                window.location.href = `${window.location.origin}/`
            }
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */


        _onSubmit: function () {
            var $btn = this.$('.oe_login_buttons > button[type="submit"]');
            $btn.attr('disabled', 'disabled');
            $btn.prepend('<i class="fa fa-refresh fa-spin"/> ');
        },
    });
});
