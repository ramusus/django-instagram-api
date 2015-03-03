# -*- coding: utf-8 -*-
from django.contrib import admin
from models import User


class AllFieldsReadOnly(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in obj._meta.fields]
        return []


class UserAdmin(AllFieldsReadOnly):
    list_display = ['username', 'full_name', 'created_at']
    search_fields = ('username', 'full_name')

    exclude = ('followers',)

admin.site.register(User, UserAdmin)
