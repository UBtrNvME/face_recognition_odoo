odoo.define('fr_core.test_script', function (require) {
    "use strict";

    var rpc = require('web.rpc');

    $(document).ready(function () {
        // var targetObj = {};
        // var targetProxy = new Proxy(targetObj, {
        //     set: function (target, key, value) {
        //         if (target[key]) {
        //             target[key] += value
        //         } else {
        //             target[key] = 0;
        //             target[key] = value
        //         }
        //         console.log(key, value)
        //         if (target[key] === 2) {
        //             document.getElementsByClassName('oe_login_buttons')[0].style.display = '';
        //         }
        //         return true;
        //     }
        // });
        var finishedJobs = 0;
        $("#iin_attachment_front").change(function () {
            let id = "#iin_attachment_front"

            let fileReader = new FileReader();
            fileReader.onload = function () {
                document.getElementById('overlay').style.display = 'flex';
                let data = fileReader.result;
                rpc.query({
                    route: '/api/processFrontIinImage',
                    params: {
                        'unknown_iin_image': data
                    }
                }).then(response => {
                    if (!response.results || response.error) {
                        window.alert("Sorry, could not recognize iin from image. Please try again, use web camera or enter it yourself.")
                    } else {
                        unpackDataFromController(response.results)
                        document.getElementsByClassName('field-front_id')[0].style.display = 'none'
                    }
                    document.getElementById('overlay').style.display = 'none';
                    finishedJobs+=1;
                    console.log(finishedJobs)
                    if (finishedJobs === 2) {
                        $('.oe_login_buttons').show();
                    }
                })

            };
            fileReader.readAsDataURL($(id).prop('files')[0]);
        });

        $("#iin_attachment_back").change(function () {
            let id = "#iin_attachment_back"

            let fileReader = new FileReader();
            fileReader.onload = function () {
                document.getElementById('overlay').style.display = 'flex';
                let data = fileReader.result;
                rpc.query({
                    route: '/api/processBackIinImage',
                    params: {
                        'unknown_iin_image': data
                    }
                }).then(response => {
                    if (!response.results || response.error) {
                        window.alert("Sorry, could not recognize iin from image. Please try again, or enter your self")
                    } else {
                        unpackDataFromController(response.results)
                        document.getElementsByClassName('field-back_id')[0].style.display = 'none'
                    }
                    document.getElementById('overlay').style.display = 'none';
                    finishedJobs+=1;
                    console.log(finishedJobs)
                    if (finishedJobs === 2) {
                        $('.oe_login_buttons').show();
                        $('.form-group').show();
                        $('.message').html("<h3>Now please check collected information</h3>")
                    }
                })
            };
            fileReader.readAsDataURL($(id).prop('files')[0]);
        });

        function unpackDataFromController(dict) {
            const keys = Object.entries(dict)
            keys.forEach((entry) => {
                const key = entry[0]
                const value = entry[1]
                if (key && value) {
                    document.getElementById(key).value = value
                }
            })
        }

    });

});
