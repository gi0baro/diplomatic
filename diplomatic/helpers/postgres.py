# -*- coding: utf-8 -*-

from emmett.orm.adapters import PostgrePsycoBoolean
from pydal.adapters import adapters
from pydal.dialects.postgre import PostgreDialectBooleanJSON
from pydal.parsers.postgre import PostgreBooleanAutoJSONParser


class PostgresAdapter(PostgrePsycoBoolean):
    def _load_dependencies(self):
        super()._load_dependencies()
        self.dialect = PostgreDialectBooleanJSON(self)
        self.parser = PostgreBooleanAutoJSONParser(self)

    def _config_json(self):
        pass

    def _mock_reconnect(self):
        pass


adapters._registry_.update({"postgres": PostgresAdapter})
