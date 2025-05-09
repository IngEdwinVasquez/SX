import { patch } from "@web/core/utils/patch";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { ReceiptExtras } from "@point_of_sale_custom/app/screens/receipt_screen/receipt/receipt_extras/receipt_extras";
import { CustomerData } from "@point_of_sale_custom/app/screens/receipt_screen/receipt/customer_data/customer_data"

patch(OrderReceipt, {
    components: {
        ...OrderReceipt.components,
        ReceiptExtras,
        CustomerData,
    },
});