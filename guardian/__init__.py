"""OpenSearch Guardian — Cluster Doctor rule framework + evidence engine.

Structure:
  guardian/
    models/           Normalized internal data models (Pydantic v2)
    rules/            Base Rule ABC + builtin rule implementations
    diagnosis/        Engine that runs all rules against a CollectionResult
"""

__version__ = "0.1.0"
