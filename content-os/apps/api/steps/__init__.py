from __future__ import annotations

# Import all step modules to trigger @StepRegistry.register() decorators.
# This ensures every step executor is registered when the steps package is imported.
from steps import (  # noqa: F401
    collect_sources,
    generate_article,
    plan_images,
    render_html,
    validate_content,
    generate_images,
    upload_images,
    create_draft,
    publish,
)
