"""
Interfaces for analyzing image forgery.

Usage::

    from apps import detection_methods
    detection_methods.analyze("sift", filepath, upload_to)
"""

import importlib


BUILTIN_DETECTION_METHODS = {
    "sift": "apps.detection_methods.sift" ,  
}

_analyzators = {}


def _load_analyzators():
    for method in BUILTIN_DETECTION_METHODS:
        module = importlib.import_module(BUILTIN_DETECTION_METHODS[method])
        _analyzators[method] = module


def _get_analyzator(method):
    if not _analyzators:
        _load_analyzators()
    
    return _analyzators[method].Analyzator


def analyze(method, filepath, upload_to=None):
    a = _get_analyzator(method)(filepath, upload_to)
    a.analyze()
    return a.get_result()



