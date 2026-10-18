"""unique username

Migration ID: 86f85243de7b
Revises: 5f93ec05dde8
Creation Date: 2026-10-18 14:50:23.178930

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '86f85243de7b'
    revises = '5f93ec05dde8'

    def up(self):
        self.create_index('users_widx__uniq_username', 'users', ['username'], expressions=[], unique=True)

    def down(self):
        self.drop_index('users_widx__uniq_username', 'users')
