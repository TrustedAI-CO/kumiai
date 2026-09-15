"""The projects.path unique index must be partial on every dialect (WORK-01 R6)."""

import pytest
from sqlalchemy.schema import CreateIndex

from app.infrastructure.database.models import Project

PATH_INDEX = "idx_projects_path_unique"


def _path_index():
    for index in Project.__table__.indexes:
        if index.name == PATH_INDEX:
            return index
    raise AssertionError(f"{PATH_INDEX} is not declared on the Project model")


class TestProjectPathUniqueIndex:
    """
    A soft-deleted project must not reserve its path.

    The original declaration set only postgresql_where. Dialect kwargs are honoured
    solely by their own dialect and silently ignored elsewhere, so on SQLite — the
    default deployment — the index was an unconditional UNIQUE. Recreating a project at
    a deleted project's path then failed with IntegrityError, and the offending row was
    invisible in the UI.
    """

    # spec: SPEC-work-project-delete-cascade R6
    @pytest.mark.parametrize("dialect_name", ["sqlite", "postgresql"])
    def test_index_is_partial_on_each_dialect(self, dialect_name):
        """The compiled DDL carries the deleted_at predicate on both dialects."""
        if dialect_name == "sqlite":
            from sqlalchemy.dialects.sqlite import dialect as make_dialect
        else:
            from sqlalchemy.dialects.postgresql import dialect as make_dialect

        ddl = str(CreateIndex(_path_index()).compile(dialect=make_dialect()))

        assert "UNIQUE" in ddl.upper(), ddl
        assert "WHERE" in ddl.upper(), (
            f"{PATH_INDEX} compiled without a predicate on {dialect_name}; a "
            f"soft-deleted project would reserve its path forever. DDL: {ddl}"
        )
        assert "deleted_at IS NULL" in ddl, ddl

    # spec: SPEC-work-project-delete-cascade R6
    def test_both_dialect_predicates_are_declared(self):
        """Guard the declaration itself, not just today's two dialects."""
        index = _path_index()
        kwargs = index.dialect_kwargs
        assert "postgresql_where" in kwargs, kwargs
        assert "sqlite_where" in kwargs, (
            "sqlite_where is missing — SQLite silently drops an unknown predicate and "
            f"builds an unconditional UNIQUE index. declared: {dict(kwargs)}"
        )
