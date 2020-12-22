odoo.define("cad.input_widget", function() {
    "use strict";
    var upload_field = "file_upload";
    $(document).ready(function() {
        console.log(`#${upload_field}`);
        $(`#${upload_field}`).change(function() {
            console.log("read");
            const fileReader = new FileReader();
            const info = document.getElementById(`${upload_field}`).files[0];
            fileReader.onload = function() {
                document.getElementById("file_content").value = fileReader.result;
                document.getElementById("file_type").value = info.type;
                console.log(info);
            };
            fileReader.readAsDataURL($(`#${upload_field}`).prop("files")[0]);
        });
    });
});
