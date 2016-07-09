""" Run sequence of time series algorithms or computations in a pipeline
"""
from ._exec import delay_pipeline, setup_pipeline
from ._task_validation import requires, outputs

__all__ = [
    'delay_pipeline',
    'setup_pipeline',
    'requires', 'outputs'
]
