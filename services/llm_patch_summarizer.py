"""Service for generating LLM summaries of patches.

This module provides functionality to summarize patch data using LLM APIs (OpenAI or Anthropic),
returning structured summaries that explain code changes and how demo_api.py runs.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

import anthropic
from sqlalchemy.orm import Session
from sqlalchemy import select

from db.models import LLMConfig
from core.encryption import decrypt_token

logger = logging.getLogger(__name__)

# Try to import OpenAI, but make it optional
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. OpenAI models will not be available.")


def _is_openai_model(model: str) -> bool:
    """Check if the model is an OpenAI model."""
    return model.startswith(("gpt-", "o1-", "o3-"))


@dataclass
class LLMPatchSummary:
    """Structured output from LLM patch summarization."""

    summary: str
    changes_description: str
    demo_api_explanation: str
    formatted_output: str


class LLMAPIKeyMissingError(Exception):
    """Raised when LLM API key is not configured."""


class LLMAPIError(Exception):
    """Raised when LLM API call fails."""


class LLMAPIQuotaExceededError(Exception):
    """Raised when LLM API quota is exceeded."""


def structure_patch_data_for_llm(patches_data: dict[str, Any]) -> dict[str, Any]:
    """Structure patch data for LLM summarization.

    Args:
        patches_data: Dictionary containing patches JSON data

    Returns:
        Structured dictionary for LLM prompt
    """
    return {
        "run_id": patches_data.get("run_id"),
        "repo": patches_data.get("repo"),
        "branch": patches_data.get("branch"),
        "commit_sha": patches_data.get("commit_sha"),
        "patches_count": patches_data.get("patches_count", 0),
        "patches": patches_data.get("patches", []),
    }


def summarize_patches_with_llm(
    patches_data: dict[str, Any],
    prompt_template: str | None = None,
    db: Session | None = None,
) -> LLMPatchSummary:
    """Generate LLM summary for patch data.

    Args:
        patches_data: Structured patch data dictionary
        prompt_template: Optional custom prompt template. If None, uses default prompt.
        db: Optional database session. If provided, uses saved LLM configuration from database.
            Otherwise, falls back to environment variables.

    Returns:
        LLMPatchSummary with summary fields

    Raises:
        LLMAPIKeyMissingError: If API key is not configured
        LLMAPIError: If API call fails
        LLMAPIQuotaExceededError: If API quota is exceeded
    """
    # Try to get configuration from database first
    api_key: str | None = None
    model: str | None = None
    
    if db:
        try:
            llm_config = db.execute(select(LLMConfig).limit(1)).scalar_one_or_none()
            if llm_config:
                api_key = decrypt_token(llm_config.encrypted_api_key)
                model = llm_config.model
                # Update last_used_at
                from datetime import datetime
                llm_config.last_used_at = datetime.utcnow()
                db.commit()
                logger.debug("Using LLM configuration from database", extra={"model": model})
        except Exception as e:
            logger.warning(f"Failed to load LLM config from database, falling back to environment: {e}")
    
    # Fall back to environment variables if not found in database
    if not api_key or not model:
        # Determine model from environment or default
        if not model:
            model = os.getenv("ANTHROPIC_MODEL") or os.getenv("OPENAI_MODEL") or "claude-sonnet-4-20250514"
        
        # Check for OpenAI first, then Anthropic
        if _is_openai_model(model):
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key or api_key == "your-llm-api-token-placeholder":
                raise LLMAPIKeyMissingError(
                    "OpenAI API key is not configured. "
                    "Please set OPENAI_API_KEY in your environment variables or configure it in the LLM settings."
                )
        else:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key or api_key == "your-llm-api-token-placeholder":
                raise LLMAPIKeyMissingError(
                    "Claude API token is not configured. "
                    "Please set ANTHROPIC_API_KEY in your environment variables or configure it in the LLM settings."
                )
        logger.debug("Using LLM configuration from environment variables", extra={"model": model})
    
    max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000"))
    temperature = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7"))

    # Build prompt for LLM
    prompt = _build_llm_prompt(patches_data, prompt_template=prompt_template)

    # Route to appropriate API based on model
    if _is_openai_model(model):
        if not OPENAI_AVAILABLE:
            raise LLMAPIError(
                "OpenAI package is not installed. Please install it with: pip install openai"
            )
        return _call_openai_api(api_key, model, prompt, max_tokens, temperature)
    else:
        return _call_anthropic_api(api_key, model, prompt, max_tokens, temperature)


def _call_openai_api(
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> LLMPatchSummary:
    """Call OpenAI API to generate summary."""
    try:
        client = openai.OpenAI(api_key=api_key)
        logger.debug(f"Calling OpenAI API with model {model}")

        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.choices[0].message.content or ""

        # Parse the response into structured fields
        summary_text = _extract_summary_section(content)
        changes_desc = _extract_changes_section(content)
        demo_api_desc = _extract_demo_api_section(content)

        return LLMPatchSummary(
            summary=summary_text or content[:500],
            changes_description=changes_desc or "See formatted output for details",
            demo_api_explanation=demo_api_desc or "See formatted output for details",
            formatted_output=content,
        )

    except openai.APIError as e:
        error_msg = f"OpenAI API returned error: {e.status_code if hasattr(e, 'status_code') else 'unknown'} - {str(e)}"
        if hasattr(e, "status_code") and e.status_code == 429:
            raise LLMAPIQuotaExceededError(error_msg) from e
        raise LLMAPIError(error_msg) from e
    except Exception as e:
        raise LLMAPIError(f"Unexpected error calling OpenAI API: {e}") from e


def _call_anthropic_api(
    api_key: str,
    model: str,
    prompt: str,
    max_tokens: int,
    temperature: float,
) -> LLMPatchSummary:
    """Call Anthropic API to generate summary."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        logger.debug(f"Calling Claude API with model {model}")

        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0].text

        # Parse the response into structured fields
        summary_text = _extract_summary_section(content)
        changes_desc = _extract_changes_section(content)
        demo_api_desc = _extract_demo_api_section(content)

        return LLMPatchSummary(
            summary=summary_text or content[:500],
            changes_description=changes_desc or "See formatted output for details",
            demo_api_explanation=demo_api_desc or "See formatted output for details",
            formatted_output=content,
        )

    except anthropic.APIError as e:
        error_detail = e.response.json() if hasattr(e.response, "json") else str(e)
        error_msg = f"Claude API returned error: {e.status_code} - {error_detail}"
        if e.status_code == 429:
            if "quota" in str(error_detail).lower() or "billing" in str(error_detail).lower():
                raise LLMAPIQuotaExceededError(error_msg) from e
        raise LLMAPIError(error_msg) from e
    except Exception as e:
        raise LLMAPIError(f"Unexpected error calling Claude API: {e}") from e


def _build_llm_prompt(patches_data: dict[str, Any], prompt_template: str | None = None) -> str:
    """Build prompt for LLM summarization.

    Args:
        patches_data: Structured patch data
        prompt_template: Optional custom prompt template. If None, uses default prompt.

    Returns:
        Formatted prompt string
    """
    patches = patches_data.get("patches", [])
    patches_text = "\n\n".join(
        [
            f"""Patch {i+1}:
- Page ID: {p.get('page_id')}
- Status: {p.get('status')}
- Before: {p.get('diff_before', '')[:500]}
- After: {p.get('diff_after', '')[:500]}
"""
            for i, p in enumerate(patches)
        ]
    )

    # Use custom template if provided, otherwise use default
    if prompt_template:
        # Format the custom prompt template with patches data
        try:
            prompt = prompt_template.format(
                repo=patches_data.get('repo', ''),
                branch=patches_data.get('branch', ''),
                commit_sha=patches_data.get('commit_sha', ''),
                patches_count=patches_data.get('patches_count', 0),
                patches_text=patches_text,
            )
        except KeyError as e:
            logger.warning(f"Missing placeholder in custom prompt template: {e}. Using default prompt.")
            prompt = _build_default_prompt(patches_data, patches_text)
    else:
        # Use default prompt
        prompt = _build_default_prompt(patches_data, patches_text)
    
    return prompt


def _build_default_prompt(patches_data: dict[str, Any], patches_text: str) -> str:
    """Build default prompt for LLM summarization.

    Args:
        patches_data: Structured patch data
        patches_text: Formatted patches text

    Returns:
        Default formatted prompt string
    """
    return f"""Please analyze the following code changes and provide a comprehensive summary.

Repository: {patches_data.get('repo')}
Branch: {patches_data.get('branch')}
Commit: {patches_data.get('commit_sha')}
Number of patches: {patches_data.get('patches_count', 0)}

Patches:
{patches_text}

Please provide:
1. A brief summary of what was changed
2. A detailed description of the changes
3. An explanation of how demo_api.py runs and what it does
4. Any important notes or considerations

Format your response with clear sections for easy parsing.
"""


def _extract_summary_section(content: str) -> str:
    """Extract summary section from LLM response."""
    # Look for common summary markers
    markers = ["## Summary", "**Summary**", "# Summary", "Summary:"]
    for marker in markers:
        if marker in content:
            # Try to extract text after marker
            parts = content.split(marker, 1)
            if len(parts) > 1:
                # Get text until next section or end
                summary_text = parts[1].split("\n\n", 1)[0].strip()
                if summary_text:
                    return summary_text
    # Fallback: first paragraph
    return content.split("\n\n")[0] if content else ""


def _extract_changes_section(content: str) -> str:
    """Extract changes description section from LLM response."""
    markers = ["## Changes", "**Changes**", "# Changes", "Changes:", "## Change Description"]
    for marker in markers:
        if marker in content:
            parts = content.split(marker, 1)
            if len(parts) > 1:
                changes_text = parts[1].split("\n\n##", 1)[0].strip()
                if changes_text:
                    return changes_text
    return ""


def _extract_demo_api_section(content: str) -> str:
    """Extract demo_api.py explanation section from LLM response."""
    markers = [
        "## demo_api.py",
        "**demo_api.py**",
        "# demo_api.py",
        "demo_api.py:",
        "## Demo API",
        "## How demo_api.py runs",
    ]
    for marker in markers:
        if marker in content:
            parts = content.split(marker, 1)
            if len(parts) > 1:
                demo_text = parts[1].split("\n\n##", 1)[0].strip()
                if demo_text:
                    return demo_text
    return ""

