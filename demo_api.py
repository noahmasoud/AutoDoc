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





# Modify an existing function to test change detection
def process_payment(amount: float, currency: str = "USD", metadata: dict = None) -> dict:
    """Process a payment transaction.

    Args:
        amount: Payment amount
        currency: Currency code
        metadata: Optional payment metadata

    Returns:
        Transaction details with transaction_id
    """
    # TODO: Add metadata support
    # 1. Validate amount and currency
    # 2. Create transaction record with metadata
    # 3. Generate transaction_id
    # 4. Return transaction details including transaction_id
    return {"amount": amount, "currency": currency, "status": "pending"}


# Add another new function
def list_transactions(filters: dict = None, limit: int = 100) -> list:
    """List transactions with optional filters.
    
    Args:
        filters: Optional filter criteria (status, date_range, etc.)
        limit: Maximum number of results
    
    Returns:
        List of transaction records
    """
    # TODO: Implement transaction listing
    # 1. Build query from filters
    # 2. Fetch transactions from database
    # 3. Apply limit
    # 4. Return list of transactions
    pass


def send_notification(user_id: str, message: str, notification_type: str = "info") -> dict:
    """Send a notification to a user.
    
    Args:
        user_id: ID of the user to notify
        message: Notification message content
        notification_type: Type of notification (info, warning, error, success)
    
    Returns:
        Notification delivery status
    """
    # TODO: Implement notification sending
    # 1. Validate user_id exists
    # 2. Format notification based on type
    # 3. Send via appropriate channel (email, SMS, push)
    # 4. Log notification delivery
    return {
        "user_id": user_id,
        "message": message,
        "type": notification_type,
        "status": "sent",
        "timestamp": "2024-01-01T00:00:00Z"
    }