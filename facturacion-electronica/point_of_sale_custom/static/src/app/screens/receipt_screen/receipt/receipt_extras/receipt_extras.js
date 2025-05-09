import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";

export class ReceiptExtras extends Component {
    static template = "point_of_sale_custom.ReceiptExtras";
    static props = {};
    setup() {
        this.pos = usePos();
        this.ui = useState(useService("ui"));
        this.posENcf = this.pos.get_order().pos_e_ncf;
        this.posSecurityCode = this.pos.get_order().pos_security_code;
        this.posDigitalSignatureDate = this.pos.get_order().pos_digital_signature_date;
        this.posFiscalQr = this.pos.get_order().pos_fiscal_qr;
    }
}