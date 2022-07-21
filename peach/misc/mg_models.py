from mongoengine import Document, DynamicDocument, fields
from peach.misc import dt


class DBaseDocument(Document):
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField(default=dt.local_now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = dt.local_now()
        self.updated_at = dt.local_now()
        return super().save(*args, **kwargs)

    def to_dict(self):
        data = self.to_mongo()
        if data and "_id" in data:
            data["id"] = data.pop("_id")
        return data

    meta = {"abstract": True, "indexes": ["updated_at"]}


class DBaseDynamicDocument(DynamicDocument):
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField(default=dt.local_now)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = dt.local_now()
        self.updated_at = dt.local_now()
        return super().save(*args, **kwargs)

    def to_dict(self):
        data = self.to_mongo()
        if data and "_id" in data:
            data["id"] = data.pop("_id")
        return data

    meta = {"abstract": True, "indexes": ["updated_at"]}
