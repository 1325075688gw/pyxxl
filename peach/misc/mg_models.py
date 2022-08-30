from mongoengine import Document, DynamicDocument, fields
from peach.misc import dt


class DBaseDocument(Document):
    created_at = fields.DateTimeField(required=True, default=dt.local_now)
    updated_at = fields.DateTimeField(required=True, default=dt.local_now)

    def save(self, *args, **kwargs):
        self.updated_at = dt.local_now()
        return super().save(*args, **kwargs)

    def to_dict(self):
        data = self.to_mongo()
        if data and "_id" in data:
            data["id"] = str(data.pop("_id"))
        return data

    meta = {
        "abstract": True,
        "auto_create_index": False,
    }


class DBaseDynamicDocument(DynamicDocument):
    created_at = fields.DateTimeField(required=True, default=dt.local_now)
    updated_at = fields.DateTimeField(required=True, default=dt.local_now)

    def save(self, *args, **kwargs):
        self.updated_at = dt.local_now()
        return super().save(*args, **kwargs)

    def to_dict(self):
        data = self.to_mongo()
        if data and "_id" in data:
            data["id"] = str(data.pop("_id"))
        return data

    meta = {
        "abstract": True,
        "auto_create_index": False,
    }
