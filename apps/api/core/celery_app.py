from types import SimpleNamespace

class NoOpTask:
    """A no‑op task decorator used in place of Celery.

    It accepts any positional or keyword arguments (e.g., name, bind, max_retries)
    and simply returns the original function unchanged.
    """
    def __call__(self, *decorator_args, **decorator_kwargs):
        # When used as @celery_app.task(...), this method receives the decorator arguments.
        # It must return a function that will receive the original function.
        def decorator(func):
            return func
        return decorator

# Export a dummy celery_app with a task attribute that behaves like the real @celery_app.task
celery_app = SimpleNamespace(task=NoOpTask())
