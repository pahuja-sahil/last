# Import required libraries
import requests
import json

# Define constants for Stripe API
STRIPE_API_ENDPOINT = "https://api.stripe.com/v1/payment_intents"
STRIPE_API_KEY = "sk_test_your_stripe_secret_key"  # Replace with your Stripe secret key
STRIPE_API_VERSION = "2022-11-15"  # Replace with your desired Stripe API version

# Define constants for payment
PAYMENT_CURRENCY = "usd"
PAYMENT_AMOUNT = 1000  # Amount in cents

class StripeIntegration:
    def __init__(self):
        self.stripe_api_key = STRIPE_API_KEY
        self.stripe_api_version = STRIPE_API_VERSION

    def create_payment_intent(self):
        """
        Create a payment intent using Stripe API.
        """
        try:
            # Set API version and authentication
            headers = {
                "Authorization": f"Bearer {self.stripe_api_key}",
                "Stripe-Version": self.stripe_api_version
            }

            # Set payment details
            data = {
                "amount": PAYMENT_AMOUNT,
                "currency": PAYMENT_CURRENCY
            }

            # Send request to Stripe API
            response = requests.post(STRIPE_API_ENDPOINT, headers=headers, json=data)

            # Check if request was successful
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error creating payment intent: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error creating payment intent: {e}")
            return None

    def confirm_payment(self, payment_intent_id):
        """
        Confirm a payment using Stripe API.
        """
        try:
            # Set API version and authentication
            headers = {
                "Authorization": f"Bearer {self.stripe_api_key}",
                "Stripe-Version": self.stripe_api_version
            }

            # Set payment intent ID
            confirm_endpoint = f"{STRIPE_API_ENDPOINT}/{payment_intent_id}/confirm"

            # Send request to Stripe API
            response = requests.post(confirm_endpoint, headers=headers)

            # Check if request was successful
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error confirming payment: {response.text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error confirming payment: {e}")
            return None


# Example usage
if __name__ == "__main__":
    stripe_integration = StripeIntegration()

    # Create payment intent
    payment_intent = stripe_integration.create_payment_intent()
    if payment_intent:
        print(f"Payment intent created: {payment_intent['id']}")

        # Confirm payment
        confirmed_payment = stripe_integration.confirm_payment(payment_intent['id'])
        if confirmed_payment:
            print(f"Payment confirmed: {confirmed_payment['id']}")
        else:
            print("Error confirming payment")
    else:
        print("Error creating payment intent")