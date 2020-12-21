odoo.define("cad_automation.field_widgets", function(require) {
    "use strict";

    var BasicFields = require("web.basic_fields");
    var field_registry = require("web.field_registry");
    var DebouncedField = BasicFields.DebouncedField;
    var core = require("web.core");
    var qweb = core.qweb;
    var _lt = core._lt;

    var FieldConnection = DebouncedField.extend({
        className: "qzhub_field_connection",
        description: _lt("FieldConnection"),
        supportedFieldTypes: ["char", "text"],
        template: "FieldConnection",
        custom_events: _.extend({}, DebouncedField.prototype.custom_events, {
            field_changed: "_onFieldChanged",
        }),
        events: _.extend({}, DebouncedField.prototype.events, {
            input: "_onInput",
            change: "_onChange",
            blur: "_onBlur",
            "click a#addConnection": "_addConnection",
            "click a.delete-button": "_deleteConnection",
        }),

        init: function() {
            this._super.apply(this, arguments);
            this.connections = this.value ? JSON.parse(this.value) : [];
            this.ids = [];
            for (let i = 0, len = this.connections.length; i < len; i++) {
                const _ids = [];
                for (const j in ["x", "y", "dx", "dy"]) {
                    _ids.push(`input-connection-${i}-${j}`);
                }
                this.ids[i] = _ids;
            }
            this.isDirty = false;
            this.lastChangeEvent = undefined;
            this.lastConnection = undefined;
        },

        reset: function(record, event) {
            this._reset(record, event);
            if (!event || event === this.lastChangeEvent) {
                this.isDirty = false;
            }
            if (
                this.isDirty ||
                (event &&
                    event.target === this &&
                    event.data.changes &&
                    event.data.changes[this.name] === this.value)
            ) {
                if (this.attrs.decorations) {
                    // If a field is modified, then it could have triggered an onchange
                    // which changed some of its decorations. Since we bypass the
                    // render function, we need to apply decorations here to make
                    // sure they are recomputed.
                    this._applyDecorations();
                }
                return Promise.resolve();
            }
            return this._render();
        },

        _setValue: function(value) {
            return this._super(value);
        },

        _renderReadonly: function() {
            this.$el.html(
                qweb.render("FieldConnectionReadonly", {
                    connections: this.connections,
                    counter: this.connections.length,
                })
            );
            this.$el.on("click", "a", function(ev) {
                ev.preventDefault();
            });
        },

        _renderEdit: function() {
            this.$el.html(
                qweb.render("FieldConnectionEdit", {
                    connections: this.connections,
                    ids: this.ids,
                })
            );
        },

        _onFieldChanged: function(event) {
            this.lastChangeEvent = event;
        },

        _onInput: function(event) {
            this.isDirty = !this._isLastSetValue(event.target.value);
            this._doDebouncedAction();
        },

        _doAction: function(target) {
            if (!this.isDestroyed()) {
                return this._parseToOriginalValue(target);
            }
        },
        _parseToOriginalValue: function(target) {
            if (target) {
                const array = target.id.split("-");
                const map1 = ["pos", "pos", "dir", "dir"];
                const map2 = ["x", "y", "x", "y"];
                const connection_index = Number.parseInt(array[2], 10);
                const in_connection_index = Number.parseInt(array[3], 10);
                this.connections[connection_index][map1[in_connection_index]][
                    map2[in_connection_index]
                ] = Number.parseInt(target.value, 10);
                return this._setValue(JSON.stringify(this.connections));
            }
        },
        _onChange: function(event) {
            if (event && event.target) {
                this._doAction(event.target);
            }
        },
        _onNavigationMove: function(ev) {
            this._super.apply(this, arguments);

            // The following code only makes sense in edit mode, with an input
            if (this.mode === "edit" && ev.data.direction !== "cancel") {
                var input = this.$(`#${this._getIdOfTheTarget(ev)}`);
                var selecting = input.selectionEnd !== input.selectionStart;
                if (
                    (ev.data.direction === "left" &&
                        (selecting || input.selectionStart !== 0)) ||
                    (ev.data.direction === "right" &&
                        (selecting || input.selectionStart !== input.value.length))
                ) {
                    ev.stopPropagation();
                }
                if (
                    ev.data.direction === "next" &&
                    this.attrs.modifiersValue &&
                    this.attrs.modifiersValue.required &&
                    this.viewType !== "list"
                ) {
                    if (!this.$input.val()) {
                        this.setInvalidClass();
                        ev.stopPropagation();
                    } else {
                        this.removeInvalidClass();
                    }
                }
            }
        },

        _getIdOfTheTarget: function(ev) {
            return ev.target.id;
        },
        _addConnection: function() {
            this.connections.push({
                pos: {
                    x: "",
                    y: "",
                },
                dir: {
                    x: "",
                    y: "",
                },
            });
            const _ids = [];
            for (const j in ["x", "y", "dx", "dy"]) {
                _ids.push(`input-connection-${this.ids.length}-${j}`);
            }
            this.ids.push(_ids);
            this._render();
        },

        _deleteConnection: function(event) {
            const target_id = event.currentTarget.id;
            this.$(`#${target_id}`).toggleClass("text-danger");
            if (window.confirm(_lt("Do you really want to delete this connection?"))) {
                const connection_index_to_delete = target_id.split("-")[2];
                this.connections.pop(connection_index_to_delete);
                this._setValue(JSON.stringify(this.connections));
                this._render();
            }
            this.$(`#${target_id}`).toggleClass("text-danger");
        },
    });

    var FieldIgnoreRegion = DebouncedField.extend({
        className: "qzhub_field_ignore_region",
        description: _lt("FieldIgnoreRegion"),
        supportedFieldTypes: ["char", "text"],
        events: _.extend({}, DebouncedField.prototype.events, {
            input: "_onInput",
            change: "_onChange",
            blur: "_onBlur",
            "click a#addSegment": "_onAddSegment",
            "click a.delete-button": "_onDeleteSegment",
        }),

        init: function() {
            this._super.apply(this, arguments);
            this.ignoreRegions = this.value ? JSON.parse(this.value) : [];
        },

        _renderReadonly: function() {
            this.$el.html(
                qweb.render("FieldIgnoreRegionReadonly", {
                    segments: this.ignoreRegions,
                })
            );
            this.$el.on("click", "a", function(ev) {
                ev.preventDefault();
            });
        },

        _renderEdit: function() {
            this.$el.html(
                qweb.render("FieldIgnoreRegionEdit", {
                    segments: this.ignoreRegions,
                })
            );
        },

        _onDeleteSegment: function(event) {
            const target_id = event.currentTarget.id;
            this.$(`#${target_id}`).toggleClass("text-danger");
            if (window.confirm(_lt("Do you really want to delete this segment?"))) {
                const segment_index_to_delete = target_id.split("-")[2];
                this.ignoreRegions.pop(segment_index_to_delete);
                this._setValue(JSON.stringify(this.ignoreRegions));
                this._render();
            }
            this.$(`#${target_id}`).toggleClass("text-danger");
        },

        _onAddSegment: function() {
            this._rpc({
                model: "cad.symbol",
                method: "get_template",
                kwargs: {rid: this.res_id},
            }).then(response => {
                console.log(response);
                this.template = response;
                const popup = window.open("", "", "width = 500, height = 500");
                this._rpc({
                    route: "/cad/mask/edit",
                    params: {template: this.template},
                }).then(response => {
                    const content = qweb.render("Popup", {datas: response});
                    popup.document.open();
                    popup.document.write(content);
                    popup.document.close();
                    this.points = [];
                    const image = popup.document.images[0];
                    console.log(popup.document.body.children[1]);
                    popup.document.body.children[1].addEventListener("click", () => {
                        this.ignoreRegions.push(this.points);
                        this._setValue(JSON.stringify(this.ignoreRegions));
                        this.points = [];
                        popup.close();
                        this._render();
                    });
                    image.setAttribute(
                        "style",
                        `mask-image: url(${this.getImageUrl(
                            "cad.symbol",
                            "mask",
                            this.res_id
                        )})`
                    );
                    const self = this;

                    image.addEventListener("click", function(e) {
                        const elm = e.target;
                        const xPos = e.pageX - elm.x;
                        const yPos = e.pageY - elm.y;
                        self.points.push([xPos, yPos]);
                        self._rpc({
                            route: "/cad/mask/edit",
                            params: {template: self.template, points: self.points},
                        }).then(response => {
                            image.src = response;
                        });
                    });
                });
            });
        },

        getImageUrl: function(model, field, id) {
            var session = this.getSession();
            var params = {
                model: model,
                field: field,
                id: id,
            };

            return session.url("/web/image", params);
        },
    });

    field_registry.add("field_ignore_region", FieldIgnoreRegion);
    field_registry.add("field_connection", FieldConnection);
    return {
        FieldConnection,
        FieldIgnoreRegion,
    };
});
