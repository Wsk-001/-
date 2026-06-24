from __future__ import annotations

import json
import re
from typing import Any, Dict, List


class PromptEngine:
    """Prompt template engine with {{variable}} injection."""

    VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")

    def render(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace {{variable_name}} with values from variables dict.

        Supports: {{sources}}, {{article}}, {{context}}, {{template_key}}, etc.
        Variables are converted to JSON strings if they are dicts/lists.
        Unresolved variables are left as-is.
        """
        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name not in variables:
                return match.group(0)
            value = variables[var_name]
            if isinstance(value, (dict, list)):
                return json.dumps(value, ensure_ascii=False, indent=2)
            if isinstance(value, bool):
                return str(value).lower()
            if value is None:
                return ""
            return str(value)

        return self.VARIABLE_PATTERN.sub(replacer, template)

    def extract_variables(self, template: str) -> List[str]:
        """Extract all variable names from template."""
        return list(set(self.VARIABLE_PATTERN.findall(template)))

    def validate_variables(self, template: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Check which variables are missing.

        Returns a dict with:
            required: list of all variable names found in template
            missing: list of required variables not provided
            provided: list of required variables that were provided
        """
        required = self.extract_variables(template)
        missing = [v for v in required if v not in variables]
        provided = [v for v in required if v in variables]
        return {
            "required": required,
            "missing": missing,
            "provided": provided,
        }
