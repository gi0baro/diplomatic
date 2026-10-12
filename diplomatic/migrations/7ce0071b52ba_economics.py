"""economics

Migration ID: 7ce0071b52ba
Revises: 8801cfa91eb3
Creation Date: 2026-10-12 19:51:47.918392

"""

from emmett.orm import migrations


class Migration(migrations.Migration):
    revision = '7ce0071b52ba'
    revises = '8801cfa91eb3'

    def up(self):
        self.add_column('user_stats', migrations.Column('score', 'integer', default=0, notnull=True))
        self.alter_column('games', 'bet',
            existing_type='decimal(18,6)',
            existing_length=255,
            type='integer',
            existing_notnull=True)
        self.add_column('vaults', migrations.Column('credit', 'integer', default=0, notnull=True))
        self.alter_column('vaults', 'balance',
            existing_type='decimal(18,6)',
            existing_length=255,
            default=0,
            type='integer',
            existing_notnull=True)
        self.add_column('transactions', migrations.Column('type', 'integer', notnull=True))
        self.add_column('transactions', migrations.Column('credit', 'integer', default=0, notnull=True))
        self.add_column('transactions', migrations.Column('debit', 'integer', default=0, notnull=True))
        self.drop_column('transactions', 'value')
        self.drop_column('transactions', 'direction')
        self.drop_index('transactions_widx__direction', 'transactions')
        self.create_index('transactions_widx__type', 'transactions', ['type'], expressions=[], unique=False)

    def down(self):
        self.drop_index('transactions_widx__type', 'transactions')
        self.create_index('transactions_widx__direction', 'transactions', ['direction'], expressions=[], unique=False)
        self.add_column('transactions', migrations.Column('direction', 'integer', notnull=True))
        self.add_column('transactions', migrations.Column('value', 'decimal(18,6)', notnull=True))
        self.drop_column('transactions', 'debit')
        self.drop_column('transactions', 'credit')
        self.drop_column('transactions', 'type')
        self.alter_column('vaults', 'balance',
            existing_type='integer',
            existing_length=255,
            default=None,
            type='decimal(18,6)',
            existing_notnull=True)
        self.drop_column('vaults', 'credit')
        self.alter_column('games', 'bet',
            existing_type='integer',
            existing_length=255,
            type='decimal(18,6)',
            existing_notnull=True)
        self.drop_column('user_stats', 'score')
