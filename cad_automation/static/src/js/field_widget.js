odoo.define("cad_automation.ConnectionFieldView", function(require) {
  "use strict";

  const AbstracFieldOwl = require("web.AbstractFieldOwl");
  const field_registry = require("web.field_registry_owl");
  const utils = require("web.utils");
  const {Component} = owl;
  const {_lt} = require("web.translation");

  class Connection extends Component {
    constructor(...args) {
      super(...args);
      this.index = utils.generateID();
      this._id = `connection-comp-${this.index}`;
    }
  }

  Connection.template = "cad_automation.Connection";
  Connection.props = ["position", "direction", "mode"];

  class FieldConnection extends AbstracFieldOwl {
    constructor(...args) {
      super(...args);
      if (!this.connections) {
        this.connections = this.value ? JSON.parse(this.value) : [];
      }
    }

    get isSet() {
      return Boolean(this.value !== "" && Array.isArray(JSON.parse(this.value)));
    }

    async willUpdateProps(nextProps) {
      await super.willUpdateProps(nextProps);
      Object.assign(this.connections, JSON.parse(this.value));
    }

    addConnection() {
      const lastConnections = this.connections[this.connections.length - 1];
      if (
        !(
          lastConnections.pos.x === "" &&
          lastConnections.pos.y === "" &&
          lastConnections.dir.x === "" &&
          lastConnections.dir.y === ""
        )
      ) {
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

        // This._setValue(JSON.stringify(this.connections))
        console.log(this.connections);
        this.render();
      }
    }

    saveConnections() {
      const connections = this._parseConnections();
      this._setValue(JSON.stringify(connections));
    }

    _parseConnections() {
      console.log("Connections", this.connections);
      this.connections.forEach((element, index) => {
        console.log("iteration", element, index);
        element.pos.x = Number(element.pos.x);
        element.pos.y = Number(element.pos.y);
        element.dir.x = Number(element.dir.x);
        element.dir.y = Number(element.dir.y);
        this.connections[index] = element;
      });
      return this.connections;
    }
  }

  FieldConnection.components = {Connection};
  FieldConnection.description = _lt("Connection");
  FieldConnection.supportedFieldTypes = ["text", "char"];
  FieldConnection.template = "cad_automation.FieldConnection";

  field_registry.add("field_connection_widget", FieldConnection);

  class Point extends Component {}
  Point.template = "cad_automation.Point";
  Point.props = ["x", "y"];

  class Segment extends Component {}
  Segment.template = "cad_automation.Segment";
  Segment.props = ["points"];
  Segment.components = {Point};

  class FieldRegionToMask extends AbstracFieldOwl {
    constructor(...args) {
      super(...args);
      this.segments = this.value ? JSON.parse(this.value) : [];

      console.log(this.segments);
    }
  }

  FieldRegionToMask.components = {Segment};
  FieldRegionToMask.description = _lt("Region to mask");
  FieldRegionToMask.supportedFieldTypes = ["text", "char"];
  FieldRegionToMask.template = "cad_automation.FieldRegionToMask";

  field_registry.add("field_region_to_mask_widget", FieldRegionToMask);

  return {
    FieldConnection,
    FieldRegionToMask,
  };
});
