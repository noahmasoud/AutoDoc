def process_payment(amount: float, currency: str = "USD") -> dict:
    """Process a payment transaction.
    
    Args:
        amount: Payment amount
        currency: Currency code
        
    Returns:
        Transaction details
    """
    return {"amount": amount, "currency": currency, "status": "pending"}

def refund_payment(transaction_id: str) -> bool:
    """Refund a payment transaction.
    
    Args:
        transaction_id: ID of the transaction to refund
        
    Returns:
        True if refund successful
    """
    return True

def validate_transaction(amount: float) -> bool:
    """Validate transaction amount.
    
    Args:
        amount: Transaction amount to validate
        
    Returns:
        True if valid
    """
    return amount > 0
