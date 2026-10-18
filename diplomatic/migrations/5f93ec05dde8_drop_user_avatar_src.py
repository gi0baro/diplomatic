"""drop user avatar_src

Migration ID: 5f93ec05dde8
Revises: 1c7627fc31b2
Creation Date: 2026-10-18 13:54:52.080444

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '5f93ec05dde8'
    revises = '1c7627fc31b2'

    def up(self):
        self.drop_column('users', 'avatar_src')

    def down(self):
        self.add_column('users', migrations.Column('avatar_src', 'string', length=512))
