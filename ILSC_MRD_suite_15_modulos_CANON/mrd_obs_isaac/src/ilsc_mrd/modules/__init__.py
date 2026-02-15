"""ILSC Modules scaffolding.

Each module implements:
- compile(cfg) -> artifact dict (finite projection Π + errors if applicable)
- check(artifact, cfg) -> locks dict + diagnostics

This is a standardized interface so that MRDs can be extended beyond SK.
"""

# Added module: observability_isaac
