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


def get_payment_receipt(payment_id: str, format: str = "pdf") -> dict:
    """Generate and retrieve a payment receipt.
    
    Args:
        payment_id: Payment ID to generate receipt for
        format: Receipt format - 'pdf' or 'json'
        
    Returns:
        Receipt data with transaction details and download URL
    """
    return {
        "payment_id": payment_id,
        "format": format,
        "receipt_url": f"https://receipts.example.com/{payment_id}.{format}",
        "generated_at": "2025-12-06T23:00:00Z"
    }
