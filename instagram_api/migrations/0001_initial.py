# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'User'
        db.create_table(u'instagram_api_user', (
            ('fetched', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('id', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=50)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('bio', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('profile_picture', self.gf('django.db.models.fields.URLField')(max_length=300)),
            ('website', self.gf('django.db.models.fields.URLField')(max_length=300)),
            ('followers_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('media_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
        ))
        db.send_create_signal(u'instagram_api', ['User'])

        # Adding M2M table for field followers on 'User'
        m2m_table_name = db.shorten_name(u'instagram_api_user_followers')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_user', models.ForeignKey(orm[u'instagram_api.user'], null=False)),
            ('to_user', models.ForeignKey(orm[u'instagram_api.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['from_user_id', 'to_user_id'])

        # Adding model 'Media'
        db.create_table(u'instagram_api_media', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('fetched', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('remote_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('caption', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('link', self.gf('django.db.models.fields.URLField')(max_length=300)),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')()),
            ('comments_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('likes_count', self.gf('django.db.models.fields.PositiveIntegerField')(null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='media_feed', to=orm['instagram_api.User'])),
        ))
        db.send_create_signal(u'instagram_api', ['Media'])

        # Adding M2M table for field likes_users on 'Media'
        m2m_table_name = db.shorten_name(u'instagram_api_media_likes_users')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('media', models.ForeignKey(orm[u'instagram_api.media'], null=False)),
            ('user', models.ForeignKey(orm[u'instagram_api.user'], null=False))
        ))
        db.create_unique(m2m_table_name, ['media_id', 'user_id'])

        # Adding model 'Comment'
        db.create_table(u'instagram_api_comment', (
            ('fetched', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='media_comments', to=orm['instagram_api.User'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['instagram_api.User'])),
            ('media', self.gf('django.db.models.fields.related.ForeignKey')(related_name='comments', to=orm['instagram_api.Media'])),
            ('id', self.gf('django.db.models.fields.BigIntegerField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.TextField')()),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'instagram_api', ['Comment'])


    def backwards(self, orm):
        # Deleting model 'User'
        db.delete_table(u'instagram_api_user')

        # Removing M2M table for field followers on 'User'
        db.delete_table(db.shorten_name(u'instagram_api_user_followers'))

        # Deleting model 'Media'
        db.delete_table(u'instagram_api_media')

        # Removing M2M table for field likes_users on 'Media'
        db.delete_table(db.shorten_name(u'instagram_api_media_likes_users'))

        # Deleting model 'Comment'
        db.delete_table(u'instagram_api_comment')


    models = {
        u'instagram_api.comment': {
            'Meta': {'object_name': 'Comment'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'media': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['instagram_api.Media']"}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'media_comments'", 'to': u"orm['instagram_api.User']"}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'comments'", 'to': u"orm['instagram_api.User']"})
        },
        u'instagram_api.media': {
            'Meta': {'object_name': 'Media'},
            'caption': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'comments_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'likes_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'likes_users': ('m2m_history.fields.ManyToManyHistoryField', [], {'related_name': "'likes_media'", 'symmetrical': 'False', 'to': u"orm['instagram_api.User']"}),
            'link': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'remote_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'media_feed'", 'to': u"orm['instagram_api.User']"})
        },
        u'instagram_api.user': {
            'Meta': {'object_name': 'User'},
            'bio': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'followers': ('m2m_history.fields.ManyToManyHistoryField', [], {'to': u"orm['instagram_api.User']", 'symmetrical': 'False'}),
            'followers_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'media_count': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True'}),
            'profile_picture': ('django.db.models.fields.URLField', [], {'max_length': '300'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '50'}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '300'})
        }
    }

    complete_apps = ['instagram_api']