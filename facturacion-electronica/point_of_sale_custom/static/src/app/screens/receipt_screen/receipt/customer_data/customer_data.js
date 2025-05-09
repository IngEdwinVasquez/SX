import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

export class CustomerData extends Component {
    static template = "point_of_sale_custom.CustomerData";
    static props = {};
    setup() {
        this.pos = usePos();
        this.ui = useState(useService("ui"));
        this.customerName = this.pos.get_order().partner_id.name;
        this.customerVat = this.pos.get_order().partner_id.vat;
    }
}