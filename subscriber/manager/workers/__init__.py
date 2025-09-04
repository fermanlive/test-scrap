"""
Workers para procesamiento de tareas.
"""

from .worker import celery_app, scrape_products_task

__all__ = ['celery_app', 'scrape_products_task']
