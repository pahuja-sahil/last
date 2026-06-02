# Import required libraries
import requests
import json

# Define Stripe API endpoint and authentication
STRIPE_API_ENDPOINT = "https://api.stripe.c
STRIPE_SECRET_KEY = "sk_test_your_secret_key"  # Replace with your Stripe secret key

# Define function to create payment intent
de
    """
    Create a payment intent using Stripe API.
    
    Args:
        amount (int): Amount in cents
        currency (str): Currency code (e.g. usd)
    
    Returns:
        dict: Payment intent response
    """
    try:
        # Set API endpoint and authentication
        url = STRIPE_API_ENDPOINT
        headers = {
            "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {
            "amount": amount,
            "currency": currency
        }
        
        # Send POST request to create payment intent
        response = requests.post(url, headers=headers, data=data)
        
        # Check if response is successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error creating payment intent: {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"Error creating payment intent: {e}")
        return None

# Define function to confirm payment intent
def confirm_payment_intent(payment_intent_id):
    """
    Confirm a payment intent using Stripe API.
    
    Args:
        payment_intent_id (str): Payment intent ID
    
    Returns:
        dict: Payment intent response
    """
    try:
        # Set API endpoint and authentication
        url = f"{STRIPE_API_ENDPOINT}/{payment_intent_id}/confirm"
        headers = {
            "Authorization": f"Bearer {STRIPE_SECRET_KEY}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        # Send POST request to confirm payment intent
        response = requests.post(url, headers=headers)
        
        # Check if response is successful
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error confirming payment intent: {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"Error confirming payment intent: {e}")
        return None

# Example usage
if __name__ == "__main__":
    amount = 1000  # Amount in centscurrency = "usd"
    if payment_intent:
        payment_intent_id = payment_intent["id"]
        confirmed_payment_intent = confirm_payment_intent(payment_intent_id)
        if confirmed_payment_intent:
            print("Payment intent confirmed successfully")
        else:
            print("Error confirming payment intent")
    else:
        print("Error creating payment intent")
