# Product Specifications - E-Shop Checkout

## Discount Codes
- **SAVE15**: Applies a 15% discount to the subtotal (before shipping).
- **WELCOME10**: Applies a 10% discount (Legacy code, may not be active).
- Only one discount code can be applied at a time.
- Invalid codes should display an error message "Invalid Discount Code".

## Shipping
- **Standard Shipping**: Free of charge. Delivery in 5-7 business days.
- **Express Shipping**: Flat rate of $10. Delivery in 2 business days.

## Cart Logic
- Subtotal is calculated as sum of (Item Price * Quantity).
- Total = Subtotal + Shipping Cost - Discount Amount.
- Minimum quantity for any item is 1.

## Payment
- Supported methods: Credit Card, PayPal.
- Payment processing is simulated. On successful validation, show "Payment Successful!".
