# coding:utf-8
from typing import List

from PyQt5.QtSql import QSqlDatabase, QSqlRecord

from ..entity import Entity, EntityFactory
from .sql_query import SqlQuery


class DaoBase:
    """ Database access operation abstract class """

    table = ''
    fields = ['id']

    def __init__(self, db: QSqlDatabase = None):
        self.setDatabase(db)

    def createTable(self):
        """ create table """
        raise NotImplementedError

    def selectBy(self, **condition) -> Entity:
        """ query a record that meet the conditions

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entity: Entity
            entity instance, `None` if no record is found
        """
        self._prepareSelectBy(condition)

        if not (self.query.exec() and self.query.first()):
            return None

        return self.loadFromRecord(self.query.record())

    def listBy(self, **condition) -> List[Entity]:
        """ query all records that meet the conditions

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entities: List[Entity]
            entity instances, empty if no records are found
        """
        self._prepareSelectBy(condition)

        if not self.query.exec():
            return []

        return self.iterRecords()

    def listLike(self, **condition) -> List[Entity]:
        """ Fuzzy query all records that meet the conditions (or relationships)

        Parameters
        ----------
        condition: dict
            query condition

        Returns
        -------
        entities: List[Entity]
            entity instances, empty if no records are found
        """
        self._prepareSelectLike(condition)

        if not self.query.exec():
            return []

        return self.iterRecords()

    def _prepareSelectBy(self, condition: dict):
        """ prepare sql select statement

        Parameters
        ----------
        table: str
            table name

        condition: dict
            query condition
        """
        if not condition:
            raise ValueError("At least one condition must be passed in")

        placeholders = [f'{k} = ?' for k in condition.keys()]
        sql = f"SELECT * FROM {self.table} WHERE {' AND '.join(placeholders)}"
        self.query.prepare(sql)
        for v in condition.values():
            self.query.addBindValue(v)

    def _prepareSelectLike(self, condition: dict):
        """ prepare sql fuzzy select statement

        Parameters
        ----------
        table: str
            table name

        condition: dict
            query condition
        """
        if not condition:
            raise ValueError("At least one condition must be passed in")

        placeholders = [f"{k} like ?" for k in condition.keys()]
        sql = f"SELECT * FROM {self.table} WHERE {' OR '.join(placeholders)}"
        self.query.prepare(sql)
        for v in condition.values():
            self.query.addBindValue(f'%{v}%')

    def listAll(self) -> List[Entity]:
        """ query all records """
        sql = f"SELECT * FROM {self.table}"
        if not self.query.exec(sql):
            return []

        return self.iterRecords()

    def listByFields(self, field: str, values: list):
        """ query the records of field values in the list """
        if field not in self.fields:
            raise ValueError(f"field name `{field}` is illegal")

        if not values:
            return []

        placeHolders = ','.join(['?']*len(values))
        sql = f"SELECT * FROM {self.table} WHERE {field} IN ({placeHolders})"
        self.query.prepare(sql)

        for value in values:
            self.query.addBindValue(value)

        if not self.query.exec():
            return []

        return self.iterRecords()

    def listByIds(self, ids: list) -> List[Entity]:
        """ query the records of the primary key value in the list """
        return self.listByFields(self.fields[0], ids)

    def iterRecords(self) -> List[Entity]:
        """ iterate over all queried records """
        entities = []

        while self.query.next():
            entity = self.loadFromRecord(self.query.record())
            entities.append(entity)

        return entities

    def update(self, id, field: str, value) -> bool:
        """ update the value of a field in a record

        Parameters
        ----------
        id:
            primary key value

        filed: str
            field name

        value:
            field value

        Returns
        -------
        success: bool
            is the update successful
        """
        sql = f"UPDATE {self.table} SET {field} = ? WHERE {self.fields[0]} = ?"
        self.query.prepare(sql)
        self.query.addBindValue(value)
        self.query.addBindValue(id)
        return self.query.exec()

    def updateById(self, entity: Entity) -> bool:
        """ update a record

        Parameters
        ----------
        entity: Entity
            entity instance

        Returns
        -------
        success: bool
            is the update successful
        """
        if len(self.fields) <= 1:
            return False

        id_ = self.fields[0]
        values = ','.join([f'{i} = :{i}' for i in self.fields[1:]])
        sql = f"UPDATE {self.table} SET {values} WHERE {id_} = :{id_}"

        self.query.prepare(sql)
        self.bindEntityToQuery(entity)

        return self.query.exec()

    def updateByIds(self, entities: List[Entity]) -> bool:
        """ update multi records

        Parameters
        ----------
        entities: List[Entity]
            entity instances

        Returns
        -------
        success: bool
            is the update successful
        """
        if not entities:
            return True

        if len(self.fields) <= 1:
            return False

        if self.connectionName:
            db = QSqlDatabase.database(self.connectionName)
        else:
            db = QSqlDatabase.database()

        db.transaction()

        id_ = self.fields[0]
        values = ','.join([f'{i} = :{i}' for i in self.fields[1:]])
        sql = f"UPDATE {self.table} SET {values} WHERE {id_} = :{id_}"

        self.query.prepare(sql)

        for entity in entities:
            self.bindEntityToQuery(entity)
            self.query.exec()

        success = db.commit()
        return success

    def insert(self, entity: Entity) -> bool:
        """ insert a record

        Parameters
        ----------
        entity: Entity
            entity instance

        Returns
        -------
        success: bool
            is the insert successful
        """
        values = ','.join([f':{i}' for i in self.fields])
        sql = f"INSERT INTO {self.table} VALUES ({values})"
        self.query.prepare(sql)
        self.bindEntityToQuery(entity)
        return self.query.exec()

    def insertBatch(self, entities: List[Entity]) -> bool:
        """ insert multi records

        Parameters
        ----------
        entities: List[Entity]
            entity instances

        Returns
        -------
        success: bool
            is the insert successful
        """
        if not entities:
            return True

        if self.connectionName:
            db = QSqlDatabase.database(self.connectionName)
        else:
            db = QSqlDatabase.database()

        db.transaction()

        values = ','.join([f':{i}' for i in self.fields])
        sql = f"INSERT INTO {self.table} VALUES ({values})"
        self.query.prepare(sql)

        for entity in entities:
            self.bindEntityToQuery(entity)
            self.query.exec()

        return db.commit()

    def deleteById(self, id) -> bool:
        """ delete a record

        Parameters
        ----------
        id:
            primary key value

        Returns
        -------
        success: bool
            is the delete successful
        """
        sql = f"DELETE FROM {self.table} WHERE {self.fields[0]} = ?"
        self.query.prepare(sql)
        self.query.addBindValue(id)
        return self.query.exec()

    def deleteByFields(self, field: str, values: list):
        """ delete multi records based on the value of a field """
        if field not in self.fields:
            raise ValueError(f"field name `{field}` is illegal")

        if not values:
            return True

        placeHolders = ','.join(['?']*len(values))
        sql = f"DELETE FROM {self.table} WHERE {field} IN ({placeHolders})"
        self.query.prepare(sql)

        for value in values:
            self.query.addBindValue(value)

        return self.query.exec()

    def deleteByIds(self, ids: list) -> bool:
        """ delete multi records

        Parameters
        ----------
        ids: list
            primary key values

        Returns
        -------
        success: bool
            is the delete successful
        """
        return self.deleteByFields(self.fields[0], ids)

    def clearTable(self):
        """ 清空表格数据 """
        return self.query.exec(f"DELETE FROM {self.table}")

    @classmethod
    def loadFromRecord(cls, record: QSqlRecord) -> Entity:
        """ create an entity instance from a record

        Parameters
        ----------
        record: QSqlRecord
            record

        Returns
        -------
        entity: Entity
            entity instance
        """
        entity = EntityFactory.create(cls.table)

        for i in range(record.count()):
            field = record.fieldName(i)
            entity[field] = record.value(i)

        return entity

    def adjustText(self, text: str):
        """ handling single quotation marks in strings """
        return text.replace("'", "''")

    def bindEntityToQuery(self, entity: Entity):
        """ bind the value of entity to query object """
        for field in self.fields:
            value = entity[field]
            self.query.bindValue(f':{field}', value)

    def setDatabase(self, db: QSqlDatabase):
        """ use the specified database """
        self.connectionName = db.connectionName() if db else ''
        self.query = SqlQuery(db) if db else SqlQuery()
        self.query.setForwardOnly(True)