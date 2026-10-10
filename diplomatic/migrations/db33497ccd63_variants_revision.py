"""Variants revision

Migration ID: db33497ccd63
Revises: b860fa334dfb
Creation Date: 2026-09-18 18:33:47.398060

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'db33497ccd63'
    revises = 'b860fa334dfb'

    def up(self):
        self.create_index('users_widx__email_unique', 'users', ['email'], expressions=[], unique=True)
        self.create_index('auth_groups_widx__role_unique', 'auth_groups', ['role'], expressions=[], unique=True)
        self.add_column('maps', migrations.Column('revision', 'integer', default=1))
        self.create_index('maps_widx__uniq_revision', 'maps', ['name', 'revision'], expressions=[], unique=True)
        self.create_index('sys_props_widx__name_unique', 'sys_props', ['name'], expressions=[], unique=True)

    def down(self):
        self.drop_index('sys_props_widx__name_unique', 'sys_props')
        self.drop_index('maps_widx__uniq_revision', 'maps')
        self.drop_column('maps', 'revision')
        self.drop_index('auth_groups_widx__role_unique', 'auth_groups')
        self.drop_index('users_widx__email_unique', 'users')
