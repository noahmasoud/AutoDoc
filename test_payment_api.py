def process_payment(amount: float, currency: str = "USD") -> dict:
    """Process a payment transaction.

    Args:
        amount: Payment amount
        currency: Currency code

    Returns:
        Transaction details
    """
    return {"amount": amount, "currency": currency, "status": "success"}


def refund_payment(transaction_id: str) -> bool:
    """Refund a payment.

    Args:
        transaction_id: Transaction to refund

    Returns:
        True if successful
    """
    return True


def validate_payment(amount: float) -> bool:
    """Validate payment amount.

    Args:
        amount: Amount to validate

    Returns:
        True if valid
    """
    return amount > 0
