"""Generated migration

Migration ID: 117283e78000
Revises: b13ccf5a89e5
Creation Date: 2018-02-17 23:05:23.871486

"""

from weppy.orm import migrations


class Migration(migrations.Migration):
    revision = '117283e78000'
    revises = 'b13ccf5a89e5'

    def up(self):
        self.drop_column('users', 'first_name')
        self.drop_column('users', 'last_name')

    def down(self):
        self.add_column('users', migrations.Column('last_name', 'string', notnull=True, length=128))
        self.add_column('users', migrations.Column('first_name', 'string', notnull=True, length=128))