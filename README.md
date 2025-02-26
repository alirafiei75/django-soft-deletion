# Django Soft Deletion 🚀

**Django Soft Deletion** is a **Django-based library** that enables **soft deletion** by using a `deleted_at` timestamp instead of permanently removing records. This allows you to mark objects as deleted while keeping them in the database.

## 📌 Features
✅ **Soft Delete Models** – Records are hidden, not deleted.  
✅ **Custom QuerySet** – Easily filter active and deleted records.  
✅ **Works with Django ORM** – No need for major changes in your models.  
✅ **Cascade Soft Delete Support** – Automatically soft deletes related objects.  
✅ **Signal Support** – Pre and post soft delete signals included.  

---

## 📦 Installation

```bash
pip install git+https://github.com/alirafiei75/django-soft-deletion.git
```

---

## 🔧 Usage

### **1️⃣ Add `SoftDeleteModel` to Your Models**
Extend `SoftDeleteModel` in your models to enable soft deletion:

```python
from soft_deletion.models import SoftDeleteModel

class MyModel(SoftDeleteModel):
    name = models.CharField(max_length=255)
```

### **2️⃣ Soft Delete an Object**

Instead of permanently deleting an object, **soft delete it**:

```python
obj = MyModel.objects.get(id=1)
obj.soft_delete()
```

### **3️⃣ Query Active or Deleted Objects**

Use the built-in **queryset filters**:

```python
# Get only active (non-deleted) records
MyModel.objects.active()

# Get only soft-deleted records
MyModel.objects.deleted()
```

---

## ⚡ Soft Delete Behavior with Foreign Keys

`django-soft-deletion` respects Django's `on_delete` behavior.

```python
class RelatedModel(SoftDeleteModel):
    name = models.CharField(max_length=255)

class MyModel(SoftDeleteModel):
    name = models.CharField(max_length=255)
    related = models.ForeignKey(RelatedModel, on_delete=models.CASCADE)
```

- **`on_delete=models.CASCADE`** → Related objects are **also soft deleted**.  
- **`on_delete=models.SET_NULL`** → The foreign key is **set to NULL** when soft deleting.  
- **`on_delete=models.PROTECT`** → Prevents soft deletion if related objects exist.  

---

## 📜 Soft Delete Signals

You can **hook into soft delete events** using signals:

```python
from soft_deletion.signals import pre_soft_delete, post_soft_delete

def pre_delete_handler(sender, instance, **kwargs):
    print(f"About to soft delete: {instance}")

pre_soft_delete.connect(pre_delete_handler, sender=MyModel)
```

---

## ✅ Running Tests

To ensure everything works correctly, run:

```bash
pytest
```
Or using Django's test framework:

```bash
python manage.py test
```
