from collections import Counter
from functools import reduce
from operator import attrgetter, or_

from django.db import transaction, models
from django.db.models import sql
from django.db.models.deletion import Collector
from django.utils.timezone import now

from soft_deletion.models import signals


class SoftDeleteCollector(Collector):
    def soft_delete(self):
        # sort instance collections
        for model, instances in self.data.items():
            self.data[model] = sorted(instances, key=attrgetter("pk"))

        # if possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        self.sort()
        # number of objects soft deleted for each model label
        soft_deleted_counter = Counter()

        # Optimize for the case with a single obj and no dependencies
        if len(self.data) == 1 and len(instances) == 1:
            instance = list(instances)[0]
            if self.can_fast_delete(instance):
                with transaction.mark_for_rollback_on_error(self.using):
                    count = sql.UpdateQuery(model).update_batch(
                        [instance.pk], {"deleted_at": now()}, self.using
                    )
                return count, {model._meta.label: count}

        with transaction.atomic(using=self.using, savepoint=False):
            # send pre_soft_delete signals
            for model, obj in self.instances_with_model():
                if not model._meta.auto_created:
                    signals.pre_soft_delete.send(
                        sender=model, instance=obj, using=self.using
                    )

            # fast soft deletes
            for qs in self.fast_deletes:
                count = qs.update(deleted_at=now())
                if count:
                    soft_deleted_counter[qs.model._meta.label] += count

            # update fields
            for (field, value), instances_list in self.field_updates.items():
                updates = []
                objs = []
                for instances in instances_list:
                    if (
                        isinstance(instances, models.QuerySet)
                        and instances._result_cache is None
                    ):
                        updates.append(instances)
                    else:
                        objs.extend(instances)
                if updates:
                    combined_updates = reduce(or_, updates)
                    combined_updates.update(**{field.name: value})
                if objs:
                    model = objs[0].__class__
                    query = sql.UpdateQuery(model)
                    query.update_batch(
                        list({obj.pk for obj in objs}), {field.name: value}, self.using
                    )

            # reverse instance collections
            for instances in self.data.values():
                instances.reverse()

            # soft delete instances
            for model, instances in self.data.items():
                query = sql.UpdateQuery(model)
                pk_list = [obj.pk for obj in instances]
                count = query.update_batch(pk_list, {"deleted_at": now()}, self.using)
                if count:
                    soft_deleted_counter[model._meta.label] += count

                if not model._meta.auto_created:
                    for obj in instances:
                        signals.post_soft_delete.send(
                            sender=model, instance=obj, using=self.using
                        )

        return sum(soft_deleted_counter.values()), dict(soft_deleted_counter)

    def _has_signal_listeners(self, model):
        return signals.pre_soft_delete.has_listeners(
            model
        ) or signals.post_soft_delete.has_listeners(model)
