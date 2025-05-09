import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";

export class SelectEcfButton extends Component {
    static template = "point_of_sale_custom.SelectEcfButton";
    static components = {
        Dropdown,
        DropdownItem,
    };
    static props = {};
    constructor() {
        super(...arguments);
        this.onItemSelected = this.onItemSelected.bind(this); // Vincular el contexto
    }
    setup() {
        this.pos = usePos();
        this.ui = useState(useService("ui"));
        this.pos.get_order().pos_ecf_type = '32';
        this.selectedItem = useState({ value: '32', ecfName: 'Factura de Consumo Electrónica' });
        this.items = [
            {'value': '31', 'ecfName': 'Factura de Crédito Fiscal Electrónico'},
            {'value': '32', 'ecfName': 'Factura de Consumo Electrónica'},
            {'value': '33', 'ecfName': 'Nota de Débito Electrónica'},
            {'value': '34', 'ecfName': 'Nota de Crédito Electrónica'},
            {'value': '44', 'ecfName': 'Regímenes Especiales Electrónico'},
            {'value': '45', 'ecfName': 'Gubernamental Electrónico'}
        ];
    }

    onItemSelected(item) {
        this.selectedItem.value = item.value;
        this.selectedItem.ecfName = item.ecfName;
        this.pos.get_order().pos_ecf_type = item.value;
    }
}