"""coast names

Migration ID: 8332058fa8ab
Revises: 7a55ab010afd
Creation Date: 2026-10-11 15:27:52.246926

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '8332058fa8ab'
    revises = '7a55ab010afd'

    def up(self):
        self.add_column('maps', migrations.Column('coast_names', 'json'))

    def down(self):
        self.drop_column('maps', 'coast_names')
