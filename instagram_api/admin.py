# -*- coding: utf-8 -*-
from django.contrib import admin
from models import User, Media, Comment


class AllFieldsReadOnly(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [field.name for field in obj._meta.fields]
        return []


class UserAdmin(AllFieldsReadOnly):
    list_display = ['username', 'full_name', 'created_at']
    search_fields = ('username', 'full_name')

    exclude = ('followers',)

class MediaAdmin(AllFieldsReadOnly):
    list_display = ['id', 'user', 'caption', 'created_at']
    search_fields = ('caption',)

class CommentAdmin(AllFieldsReadOnly):
    list_display = ['id', 'user', 'media', 'text', 'created_at']
    search_fields = ('text',)


admin.site.register(User, UserAdmin)
admin.site.register(Media, MediaAdmin)
admin.site.register(Comment, CommentAdmin)
