# app/ml/__init__.py

"""
ML package for Janus Internship Tracker

This package contains tools for processing job listings using ML techniques:
- Job classification (software vs hardware)
- Requirements extraction and summarization
- Text processing utilities

Main components:
- processor.py: Main entry point for ML processing
- processors/: Contains specific ML processors
- models/: Contains ML models
- utils/: Contains text processing utilities
"""

from app.ml.processors.job_classifier import classify_job_category
from app.ml.processors.requirements_extractor import extract_requirements_summary