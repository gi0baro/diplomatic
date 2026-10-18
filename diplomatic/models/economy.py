from emmett import T
from emmett.orm import Field, after_insert, after_update, before_insert, belongs_to, has_many, rowmethod

from ..constants import START_POINTS
from ..helpers.choice import Choice
from . import TSModel, UUIDModel


class Vault(TSModel):
    belongs_to("user")
    has_many("transactions")

    balance = Field.int(notnull=True)
    credit = Field.int(notnull=True)

    default_values = {"balance": 0, "credit": 0}

    indexes = {"uniq_user": {"fields": ["user"], "unique": True}}

    @after_insert
    def add_welcome_points(self, fields, rid):
        rid.transactions.create(type=Transaction.Type.WELCOME, credit=START_POINTS, description="Welcome points")

    @after_update
    def refresh_user_points(self, dbset, fields):
        for row in dbset.select(self.user, self.balance, self.credit):
            self.db(self.db.UserStats.user == row.user).update(points=row.balance + row.credit)

    @rowmethod("supplement")
    def _supplement(self, row, credit, won):
        total = row.balance + (row.credit - credit) + won
        if total < START_POINTS:
            return min(START_POINTS - total, credit)
        return 0


class Transaction(TSModel, UUIDModel):
    belongs_to("vault")

    class Type(Choice):
        WELCOME = 0, T("Welcome")
        BET = 1, T("Bet")
        CANCEL = 2, T("Cancel")
        POT = 3, T("Pot")
        WON = 4, T("Won")
        SUPPLEMENT = 5, T("Supplement")

    subject_type = Field.string()
    subject_id = Field.string()
    type = Field.int(notnull=True)
    credit = Field.int(notnull=True)
    debit = Field.int(notnull=True)
    description = Field(notnull=True)

    validation = {"type": {"in": Type.choices()}, "credit": {"gte": 0}, "debit": {"gte": 0}}

    default_values = {"credit": 0, "debit": 0}

    repr_values = {"type": Type.repr()}

    indexes = {"vault": True, "type": True, "subject": {"fields": ["subject_type", "subject_id"]}}

    @before_insert
    def check_one_side(self, fields):
        if (fields.credit > 0) == (fields.debit > 0):
            raise ValueError("A transaction needs exactly one of credit and debit positive")

    @after_insert
    def apply_to_vault(self, fields, rid):
        vault = Vault.where(lambda m: m.id == fields.vault)
        if fields.type == self.Type.WELCOME:
            vault.update(balance=Vault.balance + fields.credit)
        elif fields.type == self.Type.BET:
            vault.update(balance=Vault.balance - fields.debit, credit=Vault.credit + fields.debit)
        elif fields.type == self.Type.CANCEL:
            vault.update(balance=Vault.balance + fields.credit, credit=Vault.credit - fields.credit)
        elif fields.type == self.Type.POT:
            vault.update(credit=Vault.credit - fields.debit)
        elif fields.type == self.Type.WON:
            vault.update(balance=Vault.balance + fields.credit)
        elif fields.type == self.Type.SUPPLEMENT:
            vault.update(balance=Vault.balance + fields.credit)
        else:
            raise ValueError(f"Unknown transaction type {fields.type}")
