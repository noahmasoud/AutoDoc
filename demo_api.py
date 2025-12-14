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

def get_transaction_status(transaction_id: str) -> dict:
    """Return a stubbed transaction status (placeholder)."""
    return {"transaction_id": transaction_id, "status": "unknown", "note": "placeholder"}

def get_api_documentation_template() -> str:
    """Return a template body for documenting API functions in demo_api.py.
    
    This template uses AutoDoc template variables to generate documentation
    for API functions including their signatures, descriptions, and metadata.
    
    Returns:
        Template body string with placeholders for variable substitution
    """
    return """# API Documentation: {{file_path}}

## Overview

This document describes the API functions defined in `{{file_path}}`.

**Repository:** {{run.repo}}  
**Branch:** {{run.branch}}  
**Commit:** {{run.commit_sha}}

## Functions

### {{symbol}}

**Change Type:** {{change_type}}

**Signature:**on
{{signature_after}}**Description:**  
{{#if signature_before}}
**Previous Signature:**ython
{{signature_before}}{{/if}}

---

## Summary

**Total Functions:** {{change_count}}

**Added:** {{added_count}}  
**Modified:** {{modified_count}}  
**Removed:** {{removed_count}}

**Added Symbols:** {{added_symbols}}  
**Modified Symbols:** {{modified_symbols}}  
**Removed Symbols:** {{removed_symbols}}

---

*Documentation generated automatically by AutoDoc*
"""

