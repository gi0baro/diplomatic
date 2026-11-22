"""notifications

Migration ID: b0ae213819ef
Revises: 60b4e66bf20c
Creation Date: 2026-11-21 17:16:20.234582

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'b0ae213819ef'
    revises = '60b4e66bf20c'

    def up(self):
        self.create_table(
            'notifications',
            migrations.Column('id', 'string', length=32),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('kind', 'string', notnull=True, length=32),
            migrations.Column('subject_type', 'string', length=512),
            migrations.Column('subject_id', 'string', length=512),
            migrations.Column('data', 'json', notnull=True),
            migrations.Column('delivered_at', 'datetime', notnull=True),
            migrations.Column('read_at', 'datetime'),
            migrations.Column('delivery', 'integer', notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_index('notifications_widx__user_delivered', 'notifications', ['user', 'delivered_at'], expressions=[], unique=False)
        self.create_index('notifications_widx__unread', 'notifications', ['user', 'kind', 'subject_type', 'subject_id'], expressions=[], unique=False, where='("read_at" IS NULL)')
        self.create_index('notifications_widx__pending', 'notifications', ['created_at'], expressions=[], unique=False, where='("delivery" = 0)')
        self.create_table(
            'notification_settings',
            migrations.Column('id', 'id'),
            migrations.Column('created_at', 'datetime', notnull=True),
            migrations.Column('updated_at', 'datetime', notnull=True),
            migrations.Column('email_enabled', 'boolean', default=True, notnull=True),
            migrations.Column('email_disabled', 'json', notnull=True),
            migrations.Column('user', 'reference users', ondelete='CASCADE'),
            primary_keys=['id'])
        self.create_index('notification_settings_widx__uniq_user', 'notification_settings', ['user'], expressions=[], unique=True)

    def down(self):
        self.drop_index('notification_settings_widx__uniq_user', 'notification_settings')
        self.drop_table('notification_settings')
        self.drop_index('notifications_widx__pending', 'notifications')
        self.drop_index('notifications_widx__unread', 'notifications')
        self.drop_index('notifications_widx__user_delivered', 'notifications')
        self.drop_table('notifications')
