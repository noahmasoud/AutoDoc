def validate_transaction(amount: float) -> bool:
    """Validate transaction amount.
    
    Args:
        amount: Transaction amount to validate
        
    Returns:
        True if valid
    """
    return amount > 0

def cancel_transaction(transaction_id: str, reason: str) -> dict:
    """Cancel a transaction.
    
    Args:
        transaction_id: ID of transaction to cancel
        reason: Cancellation reason
        
    Returns:
        Cancellation details
    """
    return {"transaction_id": transaction_id, "status": "cancelled", "reason": reason}

def get_transaction_history(user_id: str, limit: int = 10) -> list:
    """Get transaction history for a user.
    
    Args:
        user_id: User ID to get history for
        limit: Maximum number of transactions to return
        
    Returns:
        List of transaction records
    """
    return []

def get_payment_status(payment_id: str) -> str:
    """Get the current status of a payment.
    
    Args:
        payment_id: Payment ID to check
        
    Returns:
        Payment status
    """
    return "pending"


def validate_payment_amount(amount: float, currency: str = "USD") -> dict:
    """Validate payment amount against business rules and limits.
    
    Args:
        amount: Payment amount to validate (must be positive)
        currency: ISO 4217 currency code (default: USD)
        
    Returns:
        Validation result with status and any violations
    """
    if amount <= 0:
        raise ValueError("Payment amount must be positive")
    
    max_limit = {"USD": 10000, "EUR": 9000, "GBP": 8000}.get(currency, 10000)
    
    return {
        "valid": amount <= max_limit,
        "amount": amount,
        "currency": currency,
        "max_limit": max_limit
    }





