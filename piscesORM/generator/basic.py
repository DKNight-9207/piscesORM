from __future__ import annotations
from typing import Type, Any
from ..table import Table
from abc import ABC, abstractmethod
from ..operator import LogicalOperator


class BasicGenerator(ABC):
    @staticmethod
    @abstractmethod
    def generate_create_table(table: Type[Table], exist_ok: bool = False) -> str:
        """
        Generates the SQL statement to create a table.

        Args:
            table: The table class for which to generate the SQL.
            exist_ok: If True, the statement will not raise an error if the
                      table already exists. Defaults to False.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_structure(table: Type[Table]) -> str:
        """
        Generates the SQL statement to inspect the table's structure in the database.

        Args:
            table: The table class whose structure you want to check.
        """
        ...
    
    @staticmethod
    @abstractmethod
    def generate_insert_column(table: Type[Table], org_structure: dict) -> list[str]: 
        """
        Generates the SQL statement to insert a new column.

        Args:
            table: The table class to which you want to add a column.
            org_structure: The existing table structure, which the generator
                           uses to determine which columns need to be added.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_insert(obj: Table) -> tuple[str, tuple[Any]]: 
        """
        Generates the SQL statement to insert a new row.

        Args:
            obj: The object representing the new row.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_update_object(obj: Table, merge:bool = True) -> tuple[str, tuple[Any]]: 
        """
        Generates the SQL statement to synchronize the object's data with the database.

        Args:
            obj: The object in the application whose data should be updated.
            merge: The method used for synchronization.
                   * True: Updates only the data that has changed.
                   * False: Updates all data in the row.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_update(table: Type[Table], filters: LogicalOperator, **target) -> tuple[str, tuple[Any]]:
        """
        Generates the SQL statement to update values in the database.

        Args:
            table: The table class to update.
            filters: The conditions used to select the rows to be updated.
            **target: A keyword argument mapping columns to the new values.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_delete(obj_or_table: Table | Type[Table], filters) -> tuple[str, tuple[Any]]:
        """
        Generates the SQL statement to delete records from the database.

        Args:
            obj_or_table:
                * Table instance: Deletes the record represented by the instance.
                * Table class: Deletes records based on the provided filters.
            filters: The conditions for the deletion.

        Returns:
            A tuple containing the SQL statement and the values to execute.
        """
        ...
    
    @staticmethod
    @abstractmethod
    def generate_index(table: Type[Table]) -> list[str]: 
        """
        Generates the SQL statement to create an index.

        Args:
            table: The table class for which to create the index.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_drop(table: Type[Table]) -> str:
        """
        Generates the SQL statement to drop a table.

        Args:
            table: The table class to be dropped.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_select(table: Type[Table], filters) -> tuple[str, list]: 
        """
        Generates the SQL statement for a SELECT query.

        Args:
            table: The table class from which to select.
            filters: The conditions to filter the selection. Can be None if no
                     conditions are required.

        Returns:
            A tuple containing the SQL statement and a list of values for
            database-safe delivery.
        """
        ...

    @staticmethod
    @abstractmethod
    def generate_count(table: Type[Table], filters) -> tuple[str, list]: 
        """
        Generates the SQL statement to count rows.

        Args:
            table: The table class from which to count.
            filters: The conditions to filter the count. Can be None if no
                     conditions are required.

        Returns:
            A tuple containing the SQL statement and a list of values for
            database-safe delivery.
        """
        ...