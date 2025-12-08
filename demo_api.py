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




def refund_payment_safe(transaction_id: str, amount: float) -> dict:
    """Safely process a refund after validating the transaction.
    
    Args:
        transaction_id: ID of the transaction to refund
        amount: Amount to refund (must be positive)
    
    Returns:
        Refund result including status and any validation errors
    """
    # Validate refund amount
    if not validate_transaction(amount):
        return {
            "transaction_id": transaction_id,
            "status": "failed",
            "error": "Invalid refund amount"
        }
    
    # Mock: pretend we fetch history to confirm transaction exists
    history = get_transaction_history("dummy_user")
    found = any(txn.get("transaction_id") == transaction_id for txn in history)
    
    if not found:
        return {
            "transaction_id": transaction_id,
            "status": "failed",
            "error": "Transaction not found"
        }
    
    # If all checks pass → process pending refund
    return {
        "transaction_id": transaction_id,
        "refund_status": "pending",
        "amount": amount
    }


def cancel_subscription(user_id: str, reason: str = "user_request") -> dict:
    """Cancel a user's subscription."""
    return {"user_id": user_id, "status": "cancelled", "reason": reason}
