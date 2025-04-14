"""
Shakeout Strategy Package

This package contains modules for implementing the Shakeout trading strategy,
which focuses on detecting key candles with high volume and small body.
"""

from .detect import Detector

__all__ = ['Detector']
