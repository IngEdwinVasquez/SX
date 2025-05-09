import { patch } from "@web/core/utils/patch";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { SelectEcfButton } from "@point_of_sale_custom/app/screens/product_screen/control_buttons/select_ecf_button/select_ecf_button"

patch(ProductScreen, {
    components: {
        ...ProductScreen.components,
        SelectEcfButton,
    },
});