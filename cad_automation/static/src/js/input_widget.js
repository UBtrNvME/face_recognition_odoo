odoo.define('cad_automation.input_widget', function (require) {
    "use strict";
    var upload_field = "file_upload"
    $(document).ready(function () {
        console.log(`#${upload_field}`)
        $(`#${upload_field}`).change(function () {
            console.log('read')
            let fileReader = new FileReader();
            let info = document.getElementById(`${upload_field}`).files[0]
            fileReader.onload = function () {
                let data = fileReader.result;
                document.getElementById('file_content').value = data
                document.getElementById('file_type').value = info.type
                console.log(info)
            };
            fileReader.readAsDataURL($(`#${upload_field}`).prop('files')[0]);
        });
    });

});
