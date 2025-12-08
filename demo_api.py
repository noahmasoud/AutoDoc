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


def get_payment_status(payment_id: str) -> str:
    """Get the current status of a payment.

    Args:
        payment_id: Payment ID to check

    Returns:
        Payment status
    """
    return "pending"

# Add this new function to test AutoDoc detection
def get_payment_receipt(payment_id: str, format: str = "json") -> dict:
    """Get payment receipt in specified format.
    
    Args:
        payment_id: ID of the payment
        format: Output format (json, pdf, html)
    
    Returns:
        Receipt data in requested format
    """
    # TODO: Implement receipt generation
    # 1. Fetch payment details from database
    # 2. Format receipt based on format parameter
    # 3. Return formatted receipt data
    pass


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