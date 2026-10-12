from decimal import Decimal

from emmett import T
from emmett.orm import Field, after_insert, before_insert, belongs_to, has_many

from ..helpers.choice import Choice
from . import TSModel


class Vault(TSModel):
    belongs_to("user")
    has_many("transactions")

    balance = Field.decimal(18, 6, notnull=True)

    default_values = {"balance": Decimal(0)}

    indexes = {"uniq_user": {"fields": ["user"], "unique": True}}

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


class Transaction(TSModel):
    belongs_to("vault")

    class Direction(Choice):
        IN = 0, T("In")
        OUT = 1, T("Out")

    value = Field.decimal(18, 6, notnull=True)
    direction = Field.int(notnull=True)
    description = Field(notnull=True)

    validation = {"direction": {"in": Direction.choices(), "allow": "empty"}}

    repr_values = {"direction": Direction.repr()}

    fields_rw = {"direction": False}

    indexes = {"vault": True, "direction": True}

    @before_insert
    def set_direction(self, fields):
        fields.direction = self.Direction.IN if fields.value >= 0 else self.Direction.OUT

    @after_insert
    def update_vault_balance(self, fields, rid):
        Vault.where(lambda m: m.id).update(balance=Vault.balance + fields.value)


class ChainTransaction(TSModel):
    pass
