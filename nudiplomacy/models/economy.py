# -*- coding: utf-8 -*-

from decimal import Decimal
from weppy.orm import Field, belongs_to, has_many, after_insert
from . import TSModel


class Vault(TSModel):
    belongs_to('user')
    has_many('transactions')

    balance = Field.decimal(18, 6, notnull=True)

    default_values = {
        'balance': Decimal(0)
    }

    indexes = {
        'uniq_user': {'fields': ['user'], 'unique': True}
    }

    @after_insert
    def add_welcome_funds(self, fields, rid):
        vault_n = self.all().count()
        if vault_n <= 100:
            welcome_amount = 1000
        elif 100 < vault_n <= 250:
            welcome_amount = 500
        elif 250 < vault_n <= 500:
            welcome_amount = 250
        else:
            welcome_amount = 100
        rid.transactions.create(value=welcome_amount, description="Welcome funds")

    # @rowmethod
    # def add_expense(self, row, **kwargs):
    #     return row.transactions.create(direction=Transaction.DIRECTIONS['out'], **kwargs)

    # @rowmethod
    # def add_credit(self, row, **kwargs):
    #     return row.transactions.create(direction=Transaction.DIRECTIONS['in'], **kwargs)


class Transaction(TSModel):
    belongs_to('vault')

    value = Field.decimal(18, 6, notnull=True)
    # direction = Field.int(notnull=True)
    description = Field(notnull=True)

    # DIRECTIONS = {'in': 0, 'out': 1}

    validation = {
        # 'direction': {'in': DIRECTIONS.values()},
        'value': {'gte': 0}
    }

    indexes = {
        'vault': True
    }

    @after_insert
    def update_vault_balance(self, fields, rid):
        # multiplier = -1 if fields.direction == self.DIRECTIONS['out'] else 1
        Vault.where(lambda m: m.id).update(balance=Vault.balance + fields.value)


class ChainTransaction(TSModel):
    pass
