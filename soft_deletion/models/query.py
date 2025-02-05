from django.db.models import QuerySet

from soft_deletion.models.deletion import SoftDeleteCollector


class SoftDeleteQuerySet(QuerySet):
    def soft_delete(self):
        """Soft Delete the records in the current QuerySet."""
        self._not_support_combined_queries("soft_delete")
        if self.query.is_sliced:
            raise TypeError("Cannot use 'limit' or 'offset' with soft_delete().")
        if self.query.distinct or self.query.distinct_fields:
            raise TypeError("Cannot call soft_delete() after .distinct().")
        if self._fields is not None:
            raise TypeError(
                "Cannot call soft_delete() after .values() or .values_list()"
            )

        soft_del_query = self._chain()

        # The soft delete is actually 2 queries - one to find related objects,
        # and one to update the deleted_at fields. Make sure that the discovery of related
        # objects is performed on the same database as the soft deletion.
        soft_del_query._for_write = True

        # Disable non-supported fields.
        soft_del_query.query.select_for_update = False
        soft_del_query.query.select_related = False
        soft_del_query.query.clear_ordering(force=True)

        collector = SoftDeleteCollector(using=soft_del_query.db)
        collector.collect(soft_del_query)
        soft_deleted, _rows_count = collector.soft_delete()

        # Clear the result cache, in case this QuerySet gets reused.
        self._result_cache = None
        return soft_deleted, _rows_count

    soft_delete.alters_data = True
    soft_delete.queryset_only = True

    def active(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)
