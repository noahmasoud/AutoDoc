"""AI-powered documentation generation using Claude."""

import os
import logging
from typing import Optional
import anthropic
from dotenv import load_dotenv

load_dotenv()  # ensures os.getenv finds your .env

logger = logging.getLogger(__name__)


class AIDocumentationGenerator:
    """Generate intelligent documentation using Claude."""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        self.max_tokens = int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000"))
        self.temperature = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.3"))
        self.enabled = os.getenv("ENABLE_AI_GENERATION", "true").lower() == "true"
        self.fallback_enabled = os.getenv("FALLBACK_TO_TEMPLATE", "true").lower() == "true"
        
        self.client = None
        if self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("Claude API initialized")
        else:
            logger.warning("ANTHROPIC_API_KEY not set - AI generation disabled")
        
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load prompt template from file."""
        template_path = os.getenv("PROMPT_TEMPLATE_PATH", "prompts/default.txt")
        
        try:
            with open(template_path, 'r') as f:
                template = f.read()
                logger.info(f"Loaded prompt template from {template_path}")
                return template
        except FileNotFoundError:
            logger.warning(f"Prompt template not found: {template_path}, using fallback")
            return self._get_fallback_template()
    
    def _get_fallback_template(self) -> str:
        """Return a basic inline prompt template."""
        return """Generate API documentation for this code change:

File: {file_path}
Function: {symbol}
Change: {change_type}

Code:
```python
{code_after}
```

Provide: summary, parameters, return value, and usage example."""
    
    def generate_documentation(
        self,
        change,
        run,
        code_before: Optional[str] = None,
        code_after: str = ""
    ) -> str:
        """Generate documentation for a code change.
        
        Args:
            change: Change object with file_path, symbol, change_type
            run: Run object with repo, branch, commit_sha
            code_before: Code before the change (None if new function)
            code_after: Code after the change
            
        Returns:
            Generated documentation as markdown string
        """
        # Check if AI generation is enabled
        if not self.enabled:
            logger.info("AI generation disabled, using fallback")
            return self._fallback_documentation(change, run)
        
        # Check if Claude client is available
        if not self.client:
            logger.warning("Claude client not available")
            if self.fallback_enabled:
                return self._fallback_documentation(change, run)
            raise RuntimeError("AI generation enabled but Claude API not configured")
        
        # Build the prompt
        prompt = self._build_prompt(change, run, code_before, code_after)
        
        try:
            # Call Claude API
            logger.info(f"Generating documentation for {change.symbol} using Claude")
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            documentation = message.content[0].text
            logger.info(f"Successfully generated documentation for {change.symbol}")
            
            # Log token usage for cost tracking
            if hasattr(message, 'usage'):
                input_tokens = message.usage.input_tokens
                output_tokens = message.usage.output_tokens
                
                # Cost calculation (Claude Sonnet 4 pricing)
                input_cost = input_tokens * 0.000003  # $3 per million
                output_cost = output_tokens * 0.000015  # $15 per million
                total_cost = input_cost + output_cost
                
                logger.info(
                    f"Token usage - Input: {input_tokens}, Output: {output_tokens}, "
                    f"Cost: ${total_cost:.6f}"
                )
            
            return documentation
            
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            if self.fallback_enabled:
                logger.info("Falling back to template documentation")
                return self._fallback_documentation(change, run)
            raise
        
        except Exception as e:
            logger.error(f"Unexpected error during AI generation: {e}")
            if self.fallback_enabled:
                return self._fallback_documentation(change, run)
            raise
    
    def _build_prompt(
        self,
        change,
        run,
        code_before: Optional[str],
        code_after: str
    ) -> str:
        """Build the prompt by filling in the template."""
        return self.prompt_template.format(
            file_path=change.file_path,
            symbol=change.symbol,
            change_type=change.change_type,
            repo=run.repo,
            branch=run.branch,
            commit_sha=run.commit_sha,
            code_before=code_before or "// Function did not exist",
            code_after=code_after
        )
    
    def _fallback_documentation(self, change, run) -> str:
        """Generate basic template documentation as fallback."""
        return f"""# {change.symbol}

**Change Type**: {change.change_type}  
**File**: {change.file_path}  
**Commit**: {run.commit_sha}

---

*AI documentation generation unavailable. This is a placeholder.*

**Repository**: {run.repo}  
**Branch**: {run.branch}

Please review the code changes manually and update this documentation.
"""
    
    def is_available(self) -> bool:
        """Check if AI generation is available."""
        return self.enabled and self.client is not None


# Singleton instance
_generator = None


def get_ai_generator() -> AIDocumentationGenerator:
    """Get or create the AI documentation generator instance."""
    global _generator
    if _generator is None:
        _generator = AIDocumentationGenerator()
    return _generator
