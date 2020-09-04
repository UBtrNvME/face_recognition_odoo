odoo.define('fr_core.face_recognise_sign_up', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var csrf_token = require('web.core').csrf_token
    publicWidget.registry.SignUpFaceRecognition = publicWidget.Widget.extend({
        selector: '.qzhub_signup_form_face_recognition',
        events: {
            'submit': '_onSubmit',
        },

        start: function () {
            let self = this;
            this.csrf_token = csrf_token
            self.Data = {};
            self.Events = {}
            self.Data.images_to_upload = {
                en_face: null,
                left_profile: null,
                right_profile: null,
                face_with_smile: null
            };
            self.Events.TryAgain = new Event('tryAgain');
            let stream = navigator.mediaDevices.getUserMedia({video: true})
                .then(function (mediaStream) {
                    let video = document.querySelector('#photobooth');
                    let canvas = document.createElement("canvas");
                    document.querySelector('.canvas-container').appendChild(canvas)
                    canvas.style.mask = 'url(#masking)'
                    canvas.style.transform = 'rotateY(180deg)'
                    video.srcObject = mediaStream;
                    self.Data.video = video;
                    self.Data.canvas = canvas;
                    self.Data.video.onloadedmetadata = function (e) {
                        self.Data.video.play();
                        self.process_web_page()
                    };
                    window.addEventListener('tryAgain', function (e) {
                        self.process_web_page()
                    })
                }).catch(function (err) {
                });


        },
        face_model_fill: async function () {
            console.log("face_model_fill")
            let self = this;
            let image = null;
            let images_to_upload_data = {
                en_face: ["En Face", "Look Straight Into Camera"],
                left_profile: ["Left Profile", "Look To The Right"],
                right_profile: ["Right Profile", "Look To The Left"],
                face_with_smile: ["Face With Smile", "Look Straight And Smile"]
            }
            const keys = Object.keys(self.Data.images_to_upload);
            let key;
            let progress = 0;
            self.$("#progress-bar").show();
            for (key in keys) {
                key = keys[key]
                $('.message').text(`${images_to_upload_data[key][1]}`)
                let is_correct_type = false;
                while (!is_correct_type) {
                    let payload = {
                        image_data: this._takeAPhoto(),
                        image_type: key
                    }
                    is_correct_type = await this.process_image_type(payload, images_to_upload_data)
                    if (is_correct_type) {
                        progress += 5;
                        self.$("#progress-bar").css('width', `${progress}%`);
                    }
                }
                progress += 15;
                self.$("#progress-bar").css('width', `${progress}%`);
            }
            let request_params = {
                method: 'POST',
                body: JSON.stringify({
                    images_to_attach: self.Data.images_to_upload,
                })
            }
            let model_id = window.location.pathname.split('/')[4]
            console.log(model_id)
            $('.message').text(`Wait, we are adding your encoding to the database`)
            this.send_data_to_controller(`/api/v1/face_model/${model_id}/fill?csrf_token=${csrf_token}`, request_params, 'http')
                .then(response => {
                    self.$("#progress-bar").css('width', '100%');
                    this.redirect_with_params("/web/login", {})
                })
        },
        process_image_type: async function (payload, images_to_upload_data) {
            let self = this;
            self.Data.canvas.height = 0;
            return new Promise(resolve => {
                // setTimeout(() => {
                    self.send_data_to_controller('/api/v1/face_model/checkImageType', payload)
                        .then(result => {
                            console.log(result)
                            self.Data.video.style.height = '0px';
                            self.Data.canvas.height = 300;
                            if (result.status.success) {
                                self._drawEllipseOnCanvas('green', 5, true)
                            } else {
                                self._drawEllipseOnCanvas('red', 5, true)
                            }
                            setTimeout(() => {
                                if (result.status.success && result.payload.is_correct_type) {
                                    self.Data.images_to_upload[payload.image_type] = payload.image_data;
                                    $('.message').text(`Successfully added ${images_to_upload_data[payload.image_type][0]}`)
                                    console.log(result)
                                    self.Data.video.style.height = '300px'
                                    self.Data.canvas.height = 0;
                                    resolve(true)
                                } else {
                                    self.Data.video.style.height = '300px'
                                    self.Data.canvas.height = 0;
                                    resolve(false)
                                }
                            }, 10)
                        })
                // }, 100)


            })
        },

        call_function: function (callback, args) {
            callback.apply(this, args);
        },
        web_login_face_recognition: function () {
            console.log('web_login_face_recognition')
            this.$("#progress-bar").show();
            let image = this._takeAPhoto();
            let payload = {
                unknown_user_image: image,
            }
            this.send_data_to_controller('/api/v1/processImage', payload)
                .then(result => {
                    console.log(result)
                    this.process_response(result)
                });

        },
        process_web_page: function () {
            console.log("process_web_page")
            if (window.location.pathname.includes('fill')) {
                this.face_model_fill()
            } else {
                this.web_login_face_recognition()
            }
        },
        send_data_to_controller: function (route, params, type = "json") {
            return new Promise(resolve => {
                if (type === 'json') {
                    resolve(this._rpc({
                        route: route,
                        params: params
                    }));
                } else {
                    fetch(route, params)
                        .then(response => {
                            console.log('RESPONSE ', response)
                            resolve(response)
                        }).catch(error => {
                        console.log(error)
                    })
                }
            })
        },
        redirect_with_params: function (route, params) {
            let url = new URL(`${window.location.origin}${route}`);
            let search_params = url.searchParams;
            for (const [key, value] of Object.entries(params)) {
                search_params.set(key, value)
            }
            url.search = search_params.toString();
            window.location.href = url.toString()
        },
        process_response: function (result) {
            let self = this;
            let options = self.ResponseOptions;
            console.log('result', result)
            if (result['status']['success']) {
                if (300 <= result['status']['code'] < 400) {
                    this.redirect_with_params(result['route'], result['payload'])
                }
            } else {
                // let tryAgain = window.confirm(`Error, ${result['status']['message']}, want to try again?`)
                self._tryAgain(true)
            }

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

                    self.$("#progress-bar").css('width', '100%');
                    if (result[0] === true) {
                        console.log('result', result);
                        window.location.href = `${window.location.origin}/web/login?isRecognised=${true}&login=${result[0]}&hasPassword=${result[1]}&name=${result[2]}`
                    } else {
                        if (result === false) {
                            self._tryAgain(true)
                        } else if (result[1] === "TooManyFaces") { // Too Many Faces
                            let tryAgain = window.confirm("Sorry, more than one face in the frame, try again.")
                            self._tryAgain(tryAgain)
                        } else if (result[1] === "NoFace") {
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
            canvas.height = 300;
            canvas.width = 400;
            let canvas_context = canvas.getContext('2d')
            canvas_context.drawImage(video, 0, 0, canvas.width, canvas.height);
            let photo_to_send = canvas.toDataURL("image/jpeg");
            self._drawEllipseOnCanvas('gray', 2)
            return photo_to_send
        },
        _drawEllipseOnCanvas: function(color, width, with_image = false) {
            let canvas = this.Data.canvas;
            let video = this.Data.video;
            let canvas_context = canvas.getContext('2d')
            if (with_image === true) {
                canvas_context.drawImage(video, 0, 0, canvas.width, canvas.height);
            }
            canvas_context.lineWidth = width;
            canvas_context.strokeStyle = color;
            canvas_context.ellipse(canvas.width/2, canvas.height/2, canvas.width*0.2, canvas.height*0.35, Math.PI*2, 0, Math.PI*2)
            canvas_context.stroke()
        }
        ,
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
