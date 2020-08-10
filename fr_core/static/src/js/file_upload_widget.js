odoo.define('fr_core.test_script', function (require) {
    "use strict";

    var rpc = require('web.rpc');

    $(document).ready(function () {
        $("#uin_attachment_front").change(function () {
            let id = "#uin_attachment_front"

            let fileReader = new FileReader();
            fileReader.onload = function () {
                let data = fileReader.result;
                rpc.query({
                    route: '/api/processFrontUinImage',
                    params: {
                        'unknown_uin_image': data
                    }
                }).then(result => {
                    console.log(result)
                    if (result === -1){
                        window.alert("Sorry, could not recognize UIN from image. Please try again, use web camera or enter it yourself.")
                    }else{
                        $('#uin').val(result);
                    }
                })
            };
            fileReader.readAsDataURL($(id).prop('files')[0]);
        });

        $("#uin_attachment_back").change(function () {
            let id = "#uin_attachment_back"

            let fileReader = new FileReader();
            fileReader.onload = function () {
                let data = fileReader.result;
                rpc.query({
                    route: '/api/processBackUinImage',
                    params: {
                        'unknown_uin_image': data
                    }
                }).then(result => {
                    console.log(result)
                })
            };
            fileReader.readAsDataURL($(id).prop('files')[0]);
        });

    });

});
