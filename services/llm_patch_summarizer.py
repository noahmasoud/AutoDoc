"""Service for generating LLM summaries of patches.

This module provides functionality to summarize patch data using Claude API,
returning structured summaries that explain code changes and how demo_api.py runs.
"""

import logging
import os
from dataclasses import dataclass
from typing import Any

import anthropic

logger = logging.getLogger(__name__)


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
) -> LLMPatchSummary:
    """Generate LLM summary for patch data.

    Args:
        patches_data: Structured patch data dictionary

    Returns:
        LLMPatchSummary with summary fields

    Raises:
        LLMAPIKeyMissingError: If API key is not configured
        LLMAPIError: If API call fails
        LLMAPIQuotaExceededError: If API quota is exceeded
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-llm-api-token-placeholder":
        raise LLMAPIKeyMissingError(
            "Claude API token is not configured. "
            "Please set ANTHROPIC_API_KEY in your environment variables."
        )

    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000"))
    temperature = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7"))

    try:
        client = anthropic.Anthropic(api_key=api_key)
        logger.debug(f"Calling Claude API with model {model}")

        # Build prompt for LLM
        prompt = _build_llm_prompt(patches_data)

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


def _build_llm_prompt(patches_data: dict[str, Any]) -> str:
    """Build prompt for LLM summarization.

    Args:
        patches_data: Structured patch data

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

    prompt = f"""Please analyze the following code changes and provide a comprehensive summary.

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
    return prompt


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

