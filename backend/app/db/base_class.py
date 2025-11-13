"""
Base class for all SQLAlchemy models.
SDLC Orchestrator - Stage 03 (BUILD)

Provides common functionality for all database models.
"""

from sqlalchemy.ext.declarative import declarative_base

# Base class for all models
Base = declarative_base()
