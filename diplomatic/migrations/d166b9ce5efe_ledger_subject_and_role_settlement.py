"""ledger_subject_and_role_settlement

Migration ID: d166b9ce5efe
Revises: 86f85243de7b
Creation Date: 2026-10-18 19:10:52.540617

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = 'd166b9ce5efe'
    revises = '86f85243de7b'

    def up(self):
        self.add_column('transactions', migrations.Column('subject_type', 'string', length=512))
        self.add_column('transactions', migrations.Column('subject_id', 'string', length=512))
        self.create_index('transactions_widx__subject', 'transactions', ['subject_type', 'subject_id'], expressions=[], unique=False)

    def down(self):
        self.drop_index('transactions_widx__subject', 'transactions')
        self.drop_column('transactions', 'subject_id')
        self.drop_column('transactions', 'subject_type')
