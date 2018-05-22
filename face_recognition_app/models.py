# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import models

class UserModel(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=120)
    unique_id = models.CharField(max_length=120)
    number=models.CharField(max_length=12, null=True)
    department=models.CharField(max_length=120)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DateModel(models.Model):
    user=models.ForeignKey(UserModel)
    is_present = models.BooleanField(default=False)
    date=models.DateField(max_length=220)

    def __str__(self):
        return str(self.date)