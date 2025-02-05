from django.db.models.signals import ModelSignal

pre_soft_delete = ModelSignal(use_caching=True)
post_soft_delete = ModelSignal(use_caching=True)
