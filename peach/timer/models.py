# -*- coding: utf-8 -*-
from django.db import models


class Task(models.Model):
    biz_code = models.CharField(max_length=50)
    biz_num = models.CharField(max_length=100)
    when = models.DateTimeField()
    biz_ext = models.CharField(max_length=3000, null=True)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(default=0)
    version = models.IntegerField(default=0)

    class Meta:
        db_table = "t_task"
        unique_together = ("biz_code", "biz_num")

    def __str__(self):
        return "biz_code: {}, biz_num: {}, when: {}, biz_ext: {}".format(
            self.biz_code, self.biz_num, self.when, self.biz_ext
        )
