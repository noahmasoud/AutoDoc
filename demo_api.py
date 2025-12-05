def process_payment(amount: float, currency: str = "USD") -> dict:
    """Process a payment transaction.
    
    Args:
        amount: Payment amount
        currency: Currency code
        
    Returns:
        Transaction details
    """
    return {"amount": amount, "currency": currency, "status": "pending"}
