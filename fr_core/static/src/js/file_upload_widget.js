odoo.define('fr_core.test_script', function (require) {
    "use strict";

    var rpc = require('web.rpc');

    $(document).ready(function () {
        $("#iin_attachment_front").change(function () {
            let id = "#iin_attachment_front"

            let fileReader = new FileReader();
            fileReader.onload = function () {
                let data = fileReader.result;
                rpc.query({
                    route: '/api/processFrontIinImage',
                    params: {
                        'unknown_iin_image': data
                    }
                }).then(result => {
                    console.log(result)
                    if (result === -1){
                        window.alert("Sorry, could not recognize iin from image. Please try again, use web camera or enter it yourself.")
                    }else{
                        $('#iin').val(result);
                    }
                })
            };
            fileReader.readAsDataURL($(id).prop('files')[0]);
        });

        $("#iin_attachment_back").change(function () {
            let id = "#iin_attachment_back"

            let fileReader = new FileReader();
            fileReader.onload = function () {
                let data = fileReader.result;
                rpc.query({
                    route: '/api/processBackIinImage',
                    params: {
                        'unknown_iin_image': data
                    }
                }).then(result => {
                    console.log(result)
                })
            };
            fileReader.readAsDataURL($(id).prop('files')[0]);
        });

    });

});
