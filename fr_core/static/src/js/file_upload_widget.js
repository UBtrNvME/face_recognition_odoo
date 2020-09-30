odoo.define('fr_core.test_script', function (require) {
    "use strict";

    var rpc = require('web.rpc');



    $(document).ready(function () {
        $("#iin_attachment_front").change(function () {
            let id = "#iin_attachment_front"

            let fileReader = new FileReader();
            fileReader.onload = function () {
                console.log('display', document.getElementsByClassName('form-group field-iin')[0].style.display)
                document.getElementById('overlay').style.display = 'flex';
                let data = fileReader.result;
                rpc.query({
                    route: '/api/processFrontIinImage',
                    params: {
                        'unknown_iin_image': data
                    }
                }).then(response => {
                    console.log('DATA', response);
                    if (response.results.length || response.error){
                        window.alert("Sorry, could not recognize iin from image. Please try again, use web camera or enter it yourself.")
                    }else{
                        $('.field-iin').show();
                        document.getElementsByClassName('field-front_id')[0].style.display = 'none'
                    }
                    document.getElementById('overlay').style.display = 'none';
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
