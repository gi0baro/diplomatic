"""drop sysprop and admin

Migration ID: 8801cfa91eb3
Revises: acc04fca078c
Creation Date: 2026-10-12 15:42:13.745678

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '8801cfa91eb3'
    revises = 'acc04fca078c'

    def up(self):
        self.drop_index('sys_props_widx__uniq_name', 'sys_props')
        self.drop_index('sys_props_widx__name_unique', 'sys_props')
        self.drop_table('sys_props')
        self.drop_column('users', 'is_admin')
        self.drop_index('users_widx__isadmin', 'users')

    def down(self):
        self.create_index('users_widx__isadmin', 'users', ['is_admin'], expressions=[], unique=False)
        self.add_column('users', migrations.Column('is_admin', 'boolean', default=False, notnull=True))
        self.create_table(
            'sys_props',
            migrations.Column('id', 'id'),
            migrations.Column('name', 'string', notnull=True, length=512),
            migrations.Column('data', 'json'),
            primary_keys=[])
        self.create_index('sys_props_widx__name_unique', 'sys_props', ['name'], expressions=[], unique=True)
        self.create_index('sys_props_widx__uniq_name', 'sys_props', ['name'], expressions=[], unique=True)
