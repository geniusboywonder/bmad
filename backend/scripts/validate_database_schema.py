#!/usr/bin/env python3
"""
Database Schema Validation Tool

This script automatically validates that SQLAlchemy model definitions
match the actual database schema, catching enum vs boolean mismatches
and other type inconsistencies.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
from sqlalchemy import create_engine, inspect, Column
from sqlalchemy.types import Boolean, Enum, String, Integer, DateTime, JSON, UUID, Numeric
import argparse
from dataclasses import dataclass

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import get_engine
from app.database.models import Base


@dataclass
class SchemaIssue:
    """Represents a schema validation issue."""
    table: str
    column: str
    issue_type: str
    expected: str
    actual: str
    severity: str  # 'ERROR', 'WARNING', 'INFO'


class DatabaseSchemaValidator:
    """Validates database schema against SQLAlchemy models."""

    def __init__(self):
        self.engine = get_engine()
        self.inspector = inspect(self.engine)
        self.issues: List[SchemaIssue] = []

    def validate_all(self) -> List[SchemaIssue]:
        """Run all validation checks."""
        print("🔍 Starting database schema validation...")

        self._validate_database_type()
        self._validate_table_existence()
        self._validate_column_types()
        self._validate_foreign_keys()
        self._validate_indexes()

        return self.issues

    def _validate_database_type(self):
        """Ensure we're validating against PostgreSQL."""
        db_url = str(self.engine.url)
        if 'postgresql' not in db_url:
            self.issues.append(SchemaIssue(
                table='',
                column='',
                issue_type='DATABASE_TYPE',
                expected='postgresql',
                actual=db_url.split('://')[0],
                severity='ERROR'
            ))

    def _validate_table_existence(self):
        """Check that all model tables exist in database."""
        print("  ✓ Checking table existence...")

        db_tables = set(self.inspector.get_table_names())
        model_tables = set()

        # Get all model table names
        for table in Base.metadata.tables.values():
            model_tables.add(table.name)

        # Check for missing tables
        missing_tables = model_tables - db_tables
        for table_name in missing_tables:
            self.issues.append(SchemaIssue(
                table=table_name,
                column='',
                issue_type='MISSING_TABLE',
                expected='table exists',
                actual='table missing',
                severity='ERROR'
            ))

        # Check for extra tables (may be informational)
        extra_tables = db_tables - model_tables
        for table_name in extra_tables:
            if not table_name.startswith('alembic'):  # Skip alembic tables
                self.issues.append(SchemaIssue(
                    table=table_name,
                    column='',
                    issue_type='EXTRA_TABLE',
                    expected='table not in models',
                    actual='table exists',
                    severity='INFO'
                ))

    def _validate_column_types(self):
        """Validate that column types match between models and database."""
        print("  ✓ Checking column types...")

        for table_name, table in Base.metadata.tables.items():
            if table_name not in self.inspector.get_table_names():
                continue  # Skip if table doesn't exist (handled elsewhere)

            db_columns = {col['name']: col for col in self.inspector.get_columns(table_name)}

            for column in table.columns:
                if column.name not in db_columns:
                    self.issues.append(SchemaIssue(
                        table=table_name,
                        column=column.name,
                        issue_type='MISSING_COLUMN',
                        expected=str(column.type),
                        actual='column missing',
                        severity='ERROR'
                    ))
                    continue

                db_column = db_columns[column.name]
                self._check_column_type_match(table_name, column, db_column)

    def _check_column_type_match(self, table_name: str, model_column: Column, db_column: Dict):
        """Check if a specific column type matches between model and database."""
        model_type = model_column.type
        db_type_str = str(db_column['type']).upper()

        # Check boolean vs enum mismatch (the main issue we're solving)
        if isinstance(model_type, Boolean):
            if 'BOOLEAN' not in db_type_str and 'BOOL' not in db_type_str:
                self.issues.append(SchemaIssue(
                    table=table_name,
                    column=model_column.name,
                    issue_type='TYPE_MISMATCH',
                    expected='BOOLEAN',
                    actual=db_type_str,
                    severity='ERROR'
                ))

        # Check enum vs other type mismatch
        elif isinstance(model_type, Enum):
            if not ('ENUM' in db_type_str or model_type.name.upper() in db_type_str):
                self.issues.append(SchemaIssue(
                    table=table_name,
                    column=model_column.name,
                    issue_type='TYPE_MISMATCH',
                    expected=f'ENUM({model_type.name})',
                    actual=db_type_str,
                    severity='ERROR'
                ))

        # Check string length mismatches
        elif isinstance(model_type, String):
            if model_type.length and 'CHARACTER VARYING' in db_type_str:
                # Extract length from db type string if possible
                if '(' in db_type_str and ')' in db_type_str:
                    try:
                        db_length = int(db_type_str.split('(')[1].split(')')[0])
                        if db_length != model_type.length:
                            self.issues.append(SchemaIssue(
                                table=table_name,
                                column=model_column.name,
                                issue_type='LENGTH_MISMATCH',
                                expected=f'VARCHAR({model_type.length})',
                                actual=f'VARCHAR({db_length})',
                                severity='WARNING'
                            ))
                    except (ValueError, IndexError):
                        pass  # Couldn't parse length

    def _validate_foreign_keys(self):
        """Check that foreign key constraints match model relationships."""
        print("  ✓ Checking foreign key constraints...")

        for table_name, table in Base.metadata.tables.items():
            if table_name not in self.inspector.get_table_names():
                continue

            db_foreign_keys = self.inspector.get_foreign_keys(table_name)

            # Get model foreign keys
            model_foreign_keys = []
            for column in table.columns:
                if column.foreign_keys:
                    for fk in column.foreign_keys:
                        model_foreign_keys.append({
                            'column': column.name,
                            'referenced_table': fk.column.table.name,
                            'referenced_column': fk.column.name
                        })

            # Check if model FKs exist in database
            for model_fk in model_foreign_keys:
                fk_found = False
                for db_fk in db_foreign_keys:
                    if (model_fk['column'] in db_fk['constrained_columns'] and
                        model_fk['referenced_table'] == db_fk['referred_table']):
                        fk_found = True
                        break

                if not fk_found:
                    self.issues.append(SchemaIssue(
                        table=table_name,
                        column=model_fk['column'],
                        issue_type='MISSING_FOREIGN_KEY',
                        expected=f"FK to {model_fk['referenced_table']}.{model_fk['referenced_column']}",
                        actual='no foreign key',
                        severity='ERROR'
                    ))

    def _validate_indexes(self):
        """Check for expected performance indexes."""
        print("  ✓ Checking performance indexes...")

        # Define expected indexes (these should match what's in migrations)
        expected_indexes = {
            'tasks': ['idx_tasks_project_agent_status'],
            'context_artifacts': ['idx_context_artifacts_project_type'],
            'hitl_requests': ['idx_hitl_requests_project_status'],
        }

        for table_name, expected_idx_names in expected_indexes.items():
            if table_name not in self.inspector.get_table_names():
                continue

            db_indexes = self.inspector.get_indexes(table_name)
            db_index_names = [idx['name'] for idx in db_indexes]

            for expected_idx in expected_idx_names:
                if expected_idx not in db_index_names:
                    self.issues.append(SchemaIssue(
                        table=table_name,
                        column='',
                        issue_type='MISSING_INDEX',
                        expected=expected_idx,
                        actual='index not found',
                        severity='WARNING'
                    ))

    def print_report(self, issues: List[SchemaIssue]):
        """Print a formatted validation report."""
        print("\n" + "="*80)
        print("📊 DATABASE SCHEMA VALIDATION REPORT")
        print("="*80)

        if not issues:
            print("✅ No schema issues found! Database schema matches models perfectly.")
            return

        # Group issues by severity
        errors = [i for i in issues if i.severity == 'ERROR']
        warnings = [i for i in issues if i.severity == 'WARNING']
        info = [i for i in issues if i.severity == 'INFO']

        print(f"Found {len(issues)} issues: {len(errors)} errors, {len(warnings)} warnings, {len(info)} info")
        print()

        if errors:
            print("🚨 ERRORS (Must Fix)")
            print("-" * 40)
            for issue in errors:
                print(f"  {issue.table}.{issue.column} ({issue.issue_type}):")
                print(f"    Expected: {issue.expected}")
                print(f"    Actual:   {issue.actual}")
                print()

        if warnings:
            print("⚠️  WARNINGS (Should Fix)")
            print("-" * 40)
            for issue in warnings:
                print(f"  {issue.table}.{issue.column} ({issue.issue_type}):")
                print(f"    Expected: {issue.expected}")
                print(f"    Actual:   {issue.actual}")
                print()

        if info:
            print("ℹ️  INFO (For Reference)")
            print("-" * 40)
            for issue in info:
                print(f"  {issue.table}.{issue.column} ({issue.issue_type}):")
                print(f"    Expected: {issue.expected}")
                print(f"    Actual:   {issue.actual}")
                print()

    def generate_migration_suggestions(self, issues: List[SchemaIssue]) -> List[str]:
        """Generate migration script suggestions for fixing issues."""
        suggestions = []

        type_mismatch_errors = [i for i in issues if i.issue_type == 'TYPE_MISMATCH' and i.severity == 'ERROR']

        if type_mismatch_errors:
            suggestions.append("# Suggested migration commands to fix type mismatches:")
            suggestions.append("# alembic revision -m 'fix_schema_type_mismatches'")
            suggestions.append("")

            for issue in type_mismatch_errors:
                if 'BOOLEAN' in issue.expected:
                    suggestions.append(f"# Fix {issue.table}.{issue.column} enum -> boolean:")
                    suggestions.append(f'op.execute("DELETE FROM {issue.table}")  # Clear data first')
                    suggestions.append(f'op.execute("ALTER TABLE {issue.table} ALTER COLUMN {issue.column} TYPE BOOLEAN USING FALSE")')
                    suggestions.append("")

        return suggestions


def main():
    """Main entry point for schema validation."""
    parser = argparse.ArgumentParser(description='Validate database schema against SQLAlchemy models')
    parser.add_argument('--suggest-migrations', action='store_true',
                       help='Generate migration suggestions for fixing issues')
    parser.add_argument('--fail-on-errors', action='store_true',
                       help='Exit with non-zero code if errors found')

    args = parser.parse_args()

    try:
        validator = DatabaseSchemaValidator()
        issues = validator.validate_all()
        validator.print_report(issues)

        if args.suggest_migrations:
            suggestions = validator.generate_migration_suggestions(issues)
            if suggestions:
                print("\n" + "="*80)
                print("🛠️  MIGRATION SUGGESTIONS")
                print("="*80)
                for suggestion in suggestions:
                    print(suggestion)

        # Exit with error code if there are errors and --fail-on-errors is set
        errors = [i for i in issues if i.severity == 'ERROR']
        if args.fail_on_errors and errors:
            print(f"\n❌ Validation failed with {len(errors)} errors")
            sys.exit(1)

        if not issues:
            print("\n✅ Schema validation passed!")
        else:
            print(f"\n📋 Validation completed with {len(issues)} issues to review")

    except Exception as e:
        print(f"❌ Schema validation failed with exception: {e}")
        if args.fail_on_errors:
            sys.exit(1)


if __name__ == '__main__':
    main()