# -*- coding: utf-8 -*-

from pydal.adapters import adapters
from pydal.dialects.postgre import PostgreDialectBooleanJSON
from pydal.parsers.postgre import PostgreBooleanAutoJSONParser
from weppy.orm.adapters import PostgrePsycoBoolean


class PostgresAdapter(PostgrePsycoBoolean):
    def _load_dependencies(self):
        super()._load_dependencies()
        self.dialect = PostgreDialectBooleanJSON(self)
        self.parser = PostgreBooleanAutoJSONParser(self)

    def _config_json(self):
        pass

    def _mock_reconnect(self):
        pass


adapters._registry_.update({
    'postgres': PostgresAdapter
})
