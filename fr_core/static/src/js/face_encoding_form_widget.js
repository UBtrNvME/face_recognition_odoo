odoo.define('face_recognition.field_many2one_form_preview', function (require) {
    "use strict";

    let core = require('web.core'),
        AbstractField = require('web.AbstractField'),
        fieldRegistry = require('web.field_registry'),
        kanbanRecord = require('web.KanbanRecord'),
        QWeb = core.qweb,
        utils = require('web.utils');

    let FieldMany2OneFormPreview = AbstractField.extend({
        template: "FieldMany2OneFormPreview",
        className: 'qzhub_field_many2one_form_preview',
        supportedFieldTypes: ['many2one'],
        // fieldsToFetch: {
        //     partner_id: {type: "many2one"},
        //     attachment_ids: {type: "many2many"}
        // },

        init: function (parent, action) {
            this.local_urls = [];
            this.number_of_encodigs = 0;
            this.face_encodings = "";
            this.hasEncoding = false;
            // this.on('change:effective_readonly', this, this.effective_readonly_changed);
            this._super.apply(this, arguments);
        },

        set_value: function (_value) {
            this.$el.find(_.str.sprintf('button[data-id="%s"]', _.isArray(_value) ? _value[0] : _value)).addClass('btn-primary');
            return this._super.apply(this, arguments);
        },
        willStart: function () {
            let self = this;
            return this._super.apply(this, arguments).then(function () {
                return self._rpc({
                    model: "res.partner.face.model",
                    method: "search",
                    args: [[["partner_id", "=", self.res_id]]]
                }).then(function (result) {
                    self.hasEncoding = !!result[0];
                    console.log(self.hasEncoding)
                }).then(function () {
                    if (self.hasEncoding) {
                        return self.rpc_call(self.res_id)
                    }
                });
            });
        },
        start: function () {
            var self = this;
            this.set("title", 'Face Encoding');
            return this._super().then(function () {
                self.renderForm();
            });
        },
        renderForm: function () {
            let self = this;
            console.log("render")
            // self.$('.qzhub_field_many2one_form_preview').append(QWeb.render('FieldMany2OneFormPreview', {widget: self}));
            self.$el.html($(QWeb.render('FieldMany2OneFormPreview', {widget: self})));
        },

        // button_clicked: function (e) {
        //     this.set_value(parseInt(jQuqery(arguments[0].target).attr('data-id')));
        // },
        // effective_readonly_changed() {
        //     this.$el.find('button').prop('disabled', this.get('effective_readonly'));
        // },
        get_image_url: function (model, field, id) {
            return kanbanRecord._getImageUrl(model, field, id)
        },
        rpc_call: function (res_id) {
            let self = this

            return this._rpc({
                model: "res.partner.face.model",
                method: "search_read",
                args: [[["partner_id", "=", res_id]], ["id", "face_encodings"]]
            }).then(res => {
                // for ()
                self.face_encodings = res[0]["face_encodings"]
                return this._rpc({
                    model: "res.partner.face.model",
                    method: "get_attachment_ids",
                    args: [res[0]["id"]]
                }).then(res2 => {
                    self.local_urls = res2;
                    self.number_of_encodigs = res2.length;
                })
            })

        },

    });

    fieldRegistry.add("field_many2one_form_preview", FieldMany2OneFormPreview);

    return FieldMany2OneFormPreview;
});