"""Converter for transforming Markdown to Confluence Storage Format XML.

This module provides utilities to convert Markdown text to Confluence Storage Format,
which is XML-based and required for Confluence page updates.
"""

import html
import re
from typing import Any

logger = None
try:
    import logging
    logger = logging.getLogger(__name__)
except Exception:
    pass


def markdown_to_storage_format(markdown: str) -> str:
    """Convert Markdown text to Confluence Storage Format XML.

    This is a simplified converter that handles common Markdown elements:
    - Headers (h1-h6)
    - Paragraphs
    - Bold and italic text
    - Code blocks and inline code
    - Lists (ordered and unordered)
    - Links
    - Horizontal rules

    Args:
        markdown: Markdown text to convert

    Returns:
        Confluence Storage Format XML string
    """
    if not markdown:
        return ""

    # Split into lines for processing
    lines = markdown.split("\n")
    result_lines = []
    in_list = False
    list_type = None  # 'ul' or 'ol'
    in_code_block = False
    code_block_lines = []
    code_block_lang = ""

    for line in lines:
        # Handle code blocks (triple backticks)
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                code_content = "\n".join(code_block_lines)
                result_lines.append(
                    f'<ac:structured-macro ac:name="code">'
                    f'<ac:parameter ac:name="language">{code_block_lang}</ac:parameter>'
                    f'<ac:plain-text-body><![CDATA[{code_content}]]></ac:plain-text-body>'
                    f'</ac:structured-macro>'
                )
                code_block_lines = []
                code_block_lang = ""
                in_code_block = False
            else:
                # Start code block
                in_code_block = True
                code_block_lang = line.strip()[3:].strip() or ""
                if in_list:
                    result_lines.append(f"</{list_type}>")
                    in_list = False
                    list_type = None
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # Close lists if needed before headers or horizontal rules
        if in_list and (line.strip().startswith("#") or line.strip().startswith("---") or line.strip().startswith("***")):
            result_lines.append(f"</{list_type}>")
            in_list = False
            list_type = None

        # Handle horizontal rules
        if line.strip() in ("---", "***", "___"):
            if in_list:
                result_lines.append(f"</{list_type}>")
                in_list = False
                list_type = None
            result_lines.append("<hr/>")
            continue

        # Handle headers (must be before other processing)
        if line.strip().startswith("#"):
            if in_list:
                result_lines.append(f"</{list_type}>")
                in_list = False
                list_type = None
            
            # Count # to determine header level
            header_match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
            if header_match:
                level = len(header_match.group(1))
                text = header_match.group(2).strip()
                # Escape HTML in header text
                text = html.escape(text)
                result_lines.append(f"<h{level}>{text}</h{level}>")
                continue

        # Handle unordered lists
        if re.match(r"^[-*]\s+(.+)$", line):
            if not in_list or list_type != "ul":
                if in_list:
                    result_lines.append(f"</{list_type}>")
                result_lines.append("<ul>")
                in_list = True
                list_type = "ul"
            content = re.sub(r"^[-*]\s+(.+)$", r"\1", line)
            # Process inline formatting in list items
            content = _process_inline_formatting(content)
            result_lines.append(f"<li>{content}</li>")
            continue

        # Handle ordered lists
        if re.match(r"^\d+\.\s+(.+)$", line):
            if not in_list or list_type != "ol":
                if in_list:
                    result_lines.append(f"</{list_type}>")
                result_lines.append("<ol>")
                in_list = True
                list_type = "ol"
            content = re.sub(r"^\d+\.\s+(.+)$", r"\1", line)
            # Process inline formatting in list items
            content = _process_inline_formatting(content)
            result_lines.append(f"<li>{content}</li>")
            continue

        # Close list if we hit a non-list line
        if in_list:
            result_lines.append(f"</{list_type}>")
            in_list = False
            list_type = None

        # Handle empty lines
        if not line.strip():
            result_lines.append("")
            continue

        # Regular paragraph - process inline formatting
        processed_line = _process_inline_formatting(line)
        result_lines.append(f"<p>{processed_line}</p>")

    # Close any open lists
    if in_list:
        result_lines.append(f"</{list_type}>")

    # Join all lines
    xml = "\n".join(result_lines)

    return xml


def _process_inline_formatting(text: str) -> str:
    """Process inline Markdown formatting (bold, italic, code, links).

    Args:
        text: Text with inline Markdown formatting

    Returns:
        Text with HTML tags replacing Markdown
    """
    # First, protect code blocks by replacing them with placeholders
    code_blocks = []
    def replace_code(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks)-1}__"
    
    # Protect inline code (single backticks) first
    text = re.sub(r"`([^`]+)`", replace_code, text)
    
    # Escape HTML (but not in code blocks which we'll restore)
    text = html.escape(text)
    
    # Restore code blocks (they're already escaped, so convert to <code> tags)
    for i, code_block in enumerate(code_blocks):
        # Extract the code content (remove backticks)
        code_content = code_block.strip("`")
        text = text.replace(f"__CODE_BLOCK_{i}__", f'<code>{code_content}</code>')

    # Convert links [text](url) - but not inside code tags
    # Split by code tags, process non-code parts
    parts = re.split(r'(<code>.*?</code>)', text)
    processed_parts = []
    for part in parts:
        if part.startswith('<code>') and part.endswith('</code>'):
            processed_parts.append(part)  # Keep code blocks as-is
        else:
            # Process links in non-code parts
            part = re.sub(
                r"\[([^\]]+)\]\(([^)]+)\)",
                r'<a href="\2">\1</a>',
                part,
            )
            processed_parts.append(part)
    text = ''.join(processed_parts)

    # Convert bold (**text** or __text__) - but not inside code tags
    parts = re.split(r'(<code>.*?</code>)', text)
    processed_parts = []
    for part in parts:
        if part.startswith('<code>') and part.endswith('</code>'):
            processed_parts.append(part)
        else:
            part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", part)
            part = re.sub(r"__(.+?)__", r"<strong>\1</strong>", part)
            processed_parts.append(part)
    text = ''.join(processed_parts)

    # Convert italic (*text* or _text_) - but not inside code tags or bold
    parts = re.split(r'(<code>.*?</code>|<strong>.*?</strong>)', text)
    processed_parts = []
    for part in parts:
        if part.startswith('<code>') or part.startswith('<strong>'):
            processed_parts.append(part)
        else:
            # Only match single * or _ that aren't part of **
            part = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", part)
            part = re.sub(r"(?<!_)_([^_]+?)_(?!_)", r"<em>\1</em>", part)
            processed_parts.append(part)
    text = ''.join(processed_parts)

    return text


def simple_text_to_storage_format(text: str) -> str:
    """Convert plain text to Confluence Storage Format with minimal formatting.

    This is a simpler converter that just wraps text in paragraphs and escapes HTML.

    Args:
        text: Plain text to convert

    Returns:
        Confluence Storage Format XML string
    """
    if not text:
        return ""

    # Escape HTML entities
    escaped = html.escape(text)

    # Split into paragraphs (double newline)
    paragraphs = escaped.split("\n\n")

    # Wrap each paragraph in <p> tags
    para_elements = [f"<p>{p.replace(chr(10), '<br/>')}</p>" for p in paragraphs if p.strip()]

    # Join paragraphs
    xml_content = "\n".join(para_elements)

    return xml_content


def format_llm_summary_for_confluence(summary_data: dict[str, Any]) -> str:
    """Format LLM summary data as Confluence Storage Format XML.

    Args:
        summary_data: Dictionary containing summary fields from LLM summary artifact

    Returns:
        Formatted Confluence Storage Format XML string
    """
    summary = summary_data.get("summary", "")
    changes_desc = summary_data.get("changes_description", "")
    demo_api_desc = summary_data.get("demo_api_explanation", "")

    # Build markdown content
    markdown_parts = []

    markdown_parts.append("## LLM-Generated Summary")
    markdown_parts.append("")
    if summary:
        markdown_parts.append(summary)
        markdown_parts.append("")

    if changes_desc and changes_desc != "See formatted output for details":
        markdown_parts.append("### Changes Description")
        markdown_parts.append("")
        markdown_parts.append(changes_desc)
        markdown_parts.append("")

    if demo_api_desc and demo_api_desc != "See formatted output for details":
        markdown_parts.append("### Demo API Explanation")
        markdown_parts.append("")
        markdown_parts.append(demo_api_desc)
        markdown_parts.append("")

    # Add full formatted output as a collapsible section
    formatted_output = summary_data.get("formatted_output", "")
    if formatted_output:
        markdown_parts.append("---")
        markdown_parts.append("")
        markdown_parts.append("### Full Summary Details")
        markdown_parts.append("")
        markdown_parts.append(formatted_output)

    markdown_content = "\n".join(markdown_parts)

    # Convert to Storage Format
    return markdown_to_storage_format(markdown_content)
