odoo.define('face_recognition.photobooth', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var Session = require('web.session');

var QWeb = core.qweb;


var Photobooth = AbstractAction.extend({


    start: function () {
        var self = this;
        self.session = Session;
        self.$el.html(QWeb.render("face_recognition.photobooth", {widget: self}));

    },


});

core.action_registry.add('face_recognition.photobooth',Photobooth);

return Photobooth;

});
