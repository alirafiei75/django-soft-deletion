from django.db import models, router

from soft_deletion.models.deletion import SoftDeleteCollector
from soft_deletion.models.query import SoftDeleteQuerySet


class SoftDeleteModel(models.Model):
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def soft_delete(self, using=None, keep_parents=False):
        if self.pk is None:
            raise ValueError(
                "%s object can't be soft_deleted because its %s attribute is set "
                "to None." % (self._meta.object_name, self._meta.pk.attname)
            )
        using = using or router.db_for_write(self.__class__, instance=self)
        collector = SoftDeleteCollector(using=using)
        collector.collect([self], keep_parents=keep_parents)
        return collector.soft_delete()

    soft_delete.alters_data = True
