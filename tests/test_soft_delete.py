from django.apps import apps
from django.test import TransactionTestCase, override_settings
from django.db import models, connection

from soft_deletion.models import SoftDeleteModel, pre_soft_delete, post_soft_delete


@override_settings(INSTALLED_APPS=["soft_deletion"])
class SoftDeleteTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        """Dynamically create test models and apply migrations before tests run."""
        super().setUpClass()

        cls.app_config = apps.get_app_config("soft_deletion")

        # Dynamically create RelatedModel
        cls.RelatedModel = type(
            "RelatedModel",
            (SoftDeleteModel,),
            {
                "__module__": __name__,
                "name": models.CharField(max_length=255),
                "Meta": type("Meta", (), {"app_label": "soft_deletion"}),
            },
        )

        # Dynamically create TestModel
        cls.TestModel = type(
            "TestModel",
            (SoftDeleteModel,),
            {
                "__module__": __name__,
                "name": models.CharField(max_length=255),
                "related": models.ForeignKey(
                    cls.RelatedModel, on_delete=models.CASCADE
                ),
                "Meta": type("Meta", (), {"app_label": "soft_deletion"}),
            },
        )

        # Dynamically create SetNullTestModel
        cls.SetNullTestModel = type(
            "SetNullTestModel",
            (SoftDeleteModel,),
            {
                "__module__": __name__,
                "name": models.CharField(max_length=255),
                "related": models.ForeignKey(
                    cls.RelatedModel, on_delete=models.SET_NULL, null=True
                ),
                "Meta": type("Meta", (), {"app_label": "soft_deletion"}),
            },
        )

        # Dynamically create ProtectedTestModel
        cls.ProtectedTestModel = type(
            "ProtectedTestModel",
            (SoftDeleteModel,),
            {
                "__module__": __name__,
                "name": models.CharField(max_length=255),
                "related": models.ForeignKey(
                    cls.RelatedModel, on_delete=models.PROTECT
                ),
                "Meta": type("Meta", (), {"app_label": "soft_deletion"}),
            },
        )

        # Register models in Django’s app registry
        apps.all_models["tests"]["relatedmodel"] = cls.RelatedModel
        apps.all_models["tests"]["testmodel"] = cls.TestModel
        apps.all_models["tests"]["setnulltestmodel"] = cls.SetNullTestModel
        apps.all_models["tests"]["protectedtestmodel"] = cls.ProtectedTestModel

        # Force Django to create test database tables
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(cls.RelatedModel)
            schema_editor.create_model(cls.TestModel)
            schema_editor.create_model(cls.SetNullTestModel)
            schema_editor.create_model(cls.ProtectedTestModel)

    @classmethod
    def tearDownClass(cls):
        """Clean up dynamically created models after tests are done."""
        super().tearDownClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(cls.TestModel)
            schema_editor.delete_model(cls.RelatedModel)
            schema_editor.delete_model(cls.SetNullTestModel)
            schema_editor.delete_model(cls.ProtectedTestModel)

        del apps.all_models["tests"]["relatedmodel"]
        del apps.all_models["tests"]["testmodel"]
        del apps.all_models["tests"]["setnulltestmodel"]
        del apps.all_models["tests"]["protectedtestmodel"]

    def setUp(self):
        """Set up test objects before each test."""
        self.related_obj = self.RelatedModel.objects.create(name="Related Object")
        self.test_obj = self.TestModel.objects.create(
            name="Test Object", related=self.related_obj
        )
        self.set_null_test_obj = self.SetNullTestModel.objects.create(
            name="Set Null Test Object", related=self.related_obj
        )

    def test_soft_delete_instance(self):
        """Ensure soft delete sets `deleted_at` instead of deleting."""
        self.test_obj.soft_delete()
        self.test_obj.refresh_from_db()
        self.assertIsNotNone(self.test_obj.deleted_at)  # Should be soft deleted

    def test_soft_delete_queryset(self):
        """Ensure soft delete works on QuerySets."""
        self.TestModel.objects.all().soft_delete()
        self.assertEqual(
            self.TestModel.objects.active().count(), 0
        )  # No active objects
        self.assertEqual(
            self.TestModel.objects.deleted().count(), 1
        )  # 1 soft deleted object

    def test_soft_delete_does_not_delete_forever(self):
        """Ensure soft deleted objects still exist in the database."""
        self.test_obj.soft_delete()
        self.assertTrue(
            self.TestModel.objects.filter(id=self.test_obj.id).exists()
        )  # Object still exists

    def test_soft_delete_cascade(self):
        """Ensure soft delete applies CASCADE correctly."""
        self.related_obj.soft_delete()
        self.assertIsNotNone(
            self.TestModel.objects.first().deleted_at
        )  # Related should be deleted

    def test_soft_delete_set_null(self):
        """Ensure soft delete applies SET_NULL correctly."""
        self.related_obj.soft_delete()
        self.assertIsNone(
            self.SetNullTestModel.objects.first().related
        )  # ForeignKey should be NULL

    def test_soft_delete_protect(self):
        """Ensure soft delete respects PROTECT."""
        protected_obj = self.ProtectedTestModel.objects.create(  # noqa
            name="Protected Object", related=self.related_obj
        )
        with self.assertRaises(models.ProtectedError):
            self.related_obj.soft_delete()  # Should raise an error due to PROTECT behavior

    def test_soft_delete_signals(self):
        """Ensure pre_soft_delete and post_soft_delete signals are fired."""
        pre_signal_fired = []
        post_signal_fired = []

        def pre_soft_delete_handler(sender, instance, **kwargs):
            pre_signal_fired.append(instance.id)

        def post_soft_delete_handler(sender, instance, **kwargs):
            post_signal_fired.append(instance.id)

        pre_soft_delete.connect(pre_soft_delete_handler, sender=self.TestModel)
        post_soft_delete.connect(post_soft_delete_handler, sender=self.TestModel)

        self.test_obj.soft_delete()

        self.assertIn(self.test_obj.id, pre_signal_fired)
        self.assertIn(self.test_obj.id, post_signal_fired)

        pre_soft_delete.disconnect(pre_soft_delete_handler, sender=self.TestModel)
        post_soft_delete.disconnect(post_soft_delete_handler, sender=self.TestModel)
