odoo.define('fr_core.face_recognise_sign_up', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var csrf_token = require('web.core').csrf_token
    publicWidget.registry.SignUpFaceRecognition = publicWidget.Widget.extend({
        selector: '.qzhub_signup_form_face_recognition',
        start: function () {
            console.log('start')
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
                self.send_data_to_controller('/api/v1/face_model/checkImageType', payload)
                    .then(result => {
                        if (result.status.success && result.payload.is_correct_type) {
                            self.Data.images_to_upload[payload.image_type] = payload.image_data;
                            $('.message').text(`Successfully added ${images_to_upload_data[payload.image_type][0]}`)
                            resolve(true)
                        } else {
                            resolve(false)
                        }

                    })
            })
        },

        call_function: function (callback, args) {
            callback.apply(this, args);
        },
        web_login_face_recognition: function () {
            this.$('#progress-bar').css('width', '0')
            this.$("#progress-bar").show();
            let image_dimensions = {
                x: 400,
                y: 300
            }

            console.log(image_dimensions)
            let payload = {
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                },
                method: 'POST',
                body: JSON.stringify({unknown_user_image: this._takeAPhoto(), image_dimensions: image_dimensions})
            }
            this.$('#progress-bar').css('width', '50%')
            this.$('.message').text('Обрабатываем вашу фотографию ...')
            this.$('.message').removeClass('alert-danger')
            this.$('.message').toggleClass('alert-primary')
            setTimeout(() => {
                this.send_data_to_controller('/api/v1/processImage', payload, 'http')
                    .then(result => {
                        if (result.status.success) {
                            this.$('#progress-bar').css('width', '100%')
                        } else {
                            this.$('#progress-bar').css('width', '0%')
                        }
                        this.process_response(result)
                    });
            }, 800)


        },
        process_web_page: function () {
            if (window.location.pathname.includes('fill')) {
                this.face_model_fill()
            } else {
                this.web_login_face_recognition()
            }
        },
        send_data_to_controller: async function (route, params, type = "rpc") {
            return new Promise(resolve => {
                if (type === 'rpc') {
                    resolve(this._rpc({
                        route: route,
                        params: params
                    }));
                } else {
                    fetch(route, params)
                        .then(response => response.json())
                        .then(response => {
                            console.log(response)
                            resolve(response.result)
                        }).catch(error => {
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
            console.log('result', result)
            let options = self.ResponseOptions;
            this.$('.message').toggleClass('alert-primary')
            this.$('.message').toggleClass('alert-success', result.status.success)
            this.$('.message').toggleClass('alert-warning', result.status.success && result.status.code > 300)
            this.$('.message').toggleClass('alert-danger', !result.status.success)
            this.$('.message').text(result.status.message_ru)
            setTimeout(() => {
                if (result['status']['success']) {
                    if (300 <= result['status']['code'] < 400) {
                        this.redirect_with_params(result['route'], result['payload'])
                    }
                } else {
                    // let tryAgain = window.confirm(`Error, ${result['status']['message']}, want to try again?`)
                    // document.getElementsByClassName('video-container')[0].append(result.status.img)
                    self._tryAgain(true)
                    // this.$('.message').empty()
                }
            }, 800)
            // if (result['status']['success']) {
            //     if (300 <= result['status']['code'] < 400) {
            //         setTimeout(() => {
            //             this.redirect_with_params(result['route'], result['payload'])
            //         }, 800)
            //     }
            // } else {
            //     // let tryAgain = window.confirm(`Error, ${result['status']['message']}, want to try again?`)
            //     // document.getElementsByClassName('video-container')[0].append(result.status.img)
            //     setTimeout(() => {
            //         self._tryAgain(true)
            //         // this.$('.message').empty()
            //         this.$('.message').removeClass('alert-danger')
            //     }, 800)
            //
            // }

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
            return photo_to_send
        },
        _drawEllipseOnCanvas: function (color, width, with_image = false) {
            let canvas = this.Data.canvas;
            let video = this.Data.video;
            let canvas_context = canvas.getContext('2d')
            if (with_image === true) {
                canvas_context.drawImage(video, 0, 0, canvas.width, canvas.height);
            }
            canvas_context.lineWidth = width;
            canvas_context.strokeStyle = color;
            canvas_context.ellipse(canvas.width / 2, canvas.height / 2, canvas.width * 0.2, canvas.height * 0.35, Math.PI * 2, 0, Math.PI * 2)
            canvas_context.stroke()
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
    });
});
