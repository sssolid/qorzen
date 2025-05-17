#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

"""
Validation utilities for the Database Connector Plugin.

This module provides functionality for validating database data according to
user-defined rules, enabling data quality checks and verification.
"""

import asyncio
import datetime
import json
import re
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from qorzen.utils.exceptions import DatabaseError, ValidationError

from ..models import (
    ValidationRule,
    ValidationRuleType,
    ValidationResult,
    QueryResult
)


class ValidationEngine:
    """Engine for validating database data against defined rules."""

    def __init__(
            self,
            database_manager: Any,
            logger: Any,
            validation_connection_id: Optional[str] = None
    ) -> None:
        """
        Initialize the validation engine.

        Args:
            database_manager: Qorzen database manager instance
            logger: Logger instance
            validation_connection_id: Database connection ID for validation storage
        """
        self._db_manager = database_manager
        self._logger = logger
        self._validation_connection_id = validation_connection_id
        self._validators = self._create_validators()

    async def initialize(self) -> None:
        """
        Initialize the validation engine, creating necessary database tables.

        Raises:
            DatabaseError: If initialization fails
        """
        if not self._validation_connection_id:
            self._logger.warning("No validation database connection configured")
            return

        try:
            # Create validation tables if they don't exist
            await self._create_validation_tables()

            self._logger.info("Validation engine initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize validation engine: {str(e)}")
            raise DatabaseError(
                message=f"Failed to initialize validation engine: {str(e)}",
                details={"original_error": str(e)}
            )

    async def _create_validation_tables(self) -> None:
        """
        Create the necessary tables for storing validation rules and results.

        Raises:
            DatabaseError: If table creation fails
        """
        statements = [
            # Table for validation rules
            """
            CREATE TABLE IF NOT EXISTS db_validation_rules
            (
                id
                VARCHAR
            (
                36
            ) PRIMARY KEY,
                name VARCHAR
            (
                255
            ) NOT NULL,
                description TEXT,
                connection_id VARCHAR
            (
                36
            ) NOT NULL,
                table_name VARCHAR
            (
                255
            ) NOT NULL,
                field_name VARCHAR
            (
                255
            ) NOT NULL,
                rule_type VARCHAR
            (
                50
            ) NOT NULL,
                parameters TEXT NOT NULL,
                error_message TEXT NOT NULL,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """,

            # Table for validation results
            """
            CREATE TABLE IF NOT EXISTS db_validation_results
            (
                id
                VARCHAR
            (
                36
            ) PRIMARY KEY,
                rule_id VARCHAR
            (
                36
            ) NOT NULL,
                table_name VARCHAR
            (
                255
            ) NOT NULL,
                field_name VARCHAR
            (
                255
            ) NOT NULL,
                validated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN NOT NULL,
                failures TEXT,
                total_records INTEGER NOT NULL,
                failed_records INTEGER NOT NULL,
                FOREIGN KEY
            (
                rule_id
            ) REFERENCES db_validation_rules
            (
                id
            ) ON DELETE CASCADE
                )
            """
        ]

        try:
            for stmt in statements:
                await self._db_manager.execute_raw(
                    sql=stmt,
                    connection_name=self._validation_connection_id
                )

            self._logger.debug("Validation tables created or already exist")
        except Exception as e:
            self._logger.error(f"Failed to create validation tables: {str(e)}")
            raise DatabaseError(
                message=f"Failed to create validation tables: {str(e)}",
                details={"original_error": str(e)}
            )

    def _create_validators(self) -> Dict[ValidationRuleType, Any]:
        """
        Create validator functions for each rule type.

        Returns:
            Dictionary mapping rule types to validator functions
        """
        return {
            ValidationRuleType.RANGE: self._validate_range,
            ValidationRuleType.PATTERN: self._validate_pattern,
            ValidationRuleType.NOT_NULL: self._validate_not_null,
            ValidationRuleType.UNIQUE: self._validate_unique,
            ValidationRuleType.LENGTH: self._validate_length,
            ValidationRuleType.REFERENCE: self._validate_reference,
            ValidationRuleType.ENUMERATION: self._validate_enumeration,
            ValidationRuleType.CUSTOM: self._validate_custom,
        }

    async def create_rule(self, rule: ValidationRule) -> ValidationRule:
        """
        Create a new validation rule.

        Args:
            rule: Validation rule to create

        Returns:
            Created rule with updated ID

        Raises:
            DatabaseError: If rule creation fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Insert the rule into the database
            insert_sql = """
                         INSERT INTO db_validation_rules (id, name, description, connection_id, table_name, field_name, \
                                                          rule_type, parameters, error_message, active, created_at, \
                                                          updated_at) \
                         VALUES (:id, :name, :description, :connection_id, :table_name, :field_name, \
                                 :rule_type, :parameters, :error_message, :active, :created_at, :updated_at) \
                         """

            # Convert parameters to JSON
            rule_dict = rule.dict()
            rule_dict["parameters"] = json.dumps(rule_dict["parameters"])

            await self._db_manager.execute_raw(
                sql=insert_sql,
                params=rule_dict,
                connection_name=self._validation_connection_id
            )

            self._logger.info(f"Created validation rule: {rule.name}")
            return rule

        except Exception as e:
            self._logger.error(f"Failed to create validation rule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to create validation rule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def update_rule(self, rule: ValidationRule) -> ValidationRule:
        """
        Update an existing validation rule.

        Args:
            rule: Updated validation rule

        Returns:
            Updated rule

        Raises:
            DatabaseError: If rule update fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Update the rule in the database
            update_sql = """
                         UPDATE db_validation_rules \
                         SET name          = :name, \
                             description   = :description, \
                             connection_id = :connection_id, \
                             table_name    = :table_name, \
                             field_name    = :field_name, \
                             rule_type     = :rule_type, \
                             parameters    = :parameters, \
                             error_message = :error_message, \
                             active        = :active, \
                             updated_at    = :updated_at
                         WHERE id = :id \
                         """

            # Update the timestamp
            rule.updated_at = datetime.datetime.now()
            rule_dict = rule.dict()
            rule_dict["parameters"] = json.dumps(rule_dict["parameters"])

            await self._db_manager.execute_raw(
                sql=update_sql,
                params=rule_dict,
                connection_name=self._validation_connection_id
            )

            self._logger.info(f"Updated validation rule: {rule.name}")
            return rule

        except Exception as e:
            self._logger.error(f"Failed to update validation rule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to update validation rule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def delete_rule(self, rule_id: str) -> bool:
        """
        Delete a validation rule.

        Args:
            rule_id: ID of the rule to delete

        Returns:
            True if the rule was deleted

        Raises:
            DatabaseError: If rule deletion fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Delete the rule from the database
            delete_sql = "DELETE FROM db_validation_rules WHERE id = :id"

            await self._db_manager.execute_raw(
                sql=delete_sql,
                params={"id": rule_id},
                connection_name=self._validation_connection_id
            )

            self._logger.info(f"Deleted validation rule: {rule_id}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to delete validation rule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to delete validation rule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """
        Get a specific validation rule.

        Args:
            rule_id: Rule ID

        Returns:
            Validation rule or None if not found

        Raises:
            DatabaseError: If fetching the rule fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Fetch the rule from the database
            results = await self._db_manager.execute_raw(
                sql="SELECT * FROM db_validation_rules WHERE id = :id",
                params={"id": rule_id},
                connection_name=self._validation_connection_id
            )

            if not results:
                return None

            # Convert to ValidationRule
            row = results[0]
            rule_dict = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "connection_id": row["connection_id"],
                "table_name": row["table_name"],
                "field_name": row["field_name"],
                "rule_type": row["rule_type"],
                "parameters": json.loads(row["parameters"]),
                "error_message": row["error_message"],
                "active": row["active"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"]
            }

            return ValidationRule(**rule_dict)

        except Exception as e:
            self._logger.error(f"Failed to get validation rule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get validation rule: {str(e)}",
                details={"original_error": str(e)}
            )

    async def get_all_rules(
            self,
            connection_id: Optional[str] = None,
            table_name: Optional[str] = None
    ) -> List[ValidationRule]:
        """
        Get all validation rules, optionally filtered.

        Args:
            connection_id: Optional connection ID to filter by
            table_name: Optional table name to filter by

        Returns:
            List of validation rules

        Raises:
            DatabaseError: If fetching rules fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Build the SQL query
            sql = "SELECT * FROM db_validation_rules"
            params = {}

            if connection_id or table_name:
                sql += " WHERE"

                if connection_id:
                    sql += " connection_id = :connection_id"
                    params["connection_id"] = connection_id

                    if table_name:
                        sql += " AND table_name = :table_name"
                        params["table_name"] = table_name
                elif table_name:
                    sql += " table_name = :table_name"
                    params["table_name"] = table_name

            sql += " ORDER BY name"

            # Execute the query
            results = await self._db_manager.execute_raw(
                sql=sql,
                params=params,
                connection_name=self._validation_connection_id
            )

            # Convert to ValidationRule objects
            rules: List[ValidationRule] = []
            for row in results:
                rule_dict = {
                    "id": row["id"],
                    "name": row["name"],
                    "description": row["description"],
                    "connection_id": row["connection_id"],
                    "table_name": row["table_name"],
                    "field_name": row["field_name"],
                    "rule_type": row["rule_type"],
                    "parameters": json.loads(row["parameters"]),
                    "error_message": row["error_message"],
                    "active": row["active"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                rules.append(ValidationRule(**rule_dict))

            return rules

        except Exception as e:
            self._logger.error(f"Failed to get validation rules: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get validation rules: {str(e)}",
                details={"original_error": str(e)}
            )

    async def validate_data(
            self,
            rule: ValidationRule,
            data: QueryResult
    ) -> ValidationResult:
        """
        Validate data against a rule.

        Args:
            rule: Validation rule to apply
            data: Query result to validate

        Returns:
            Validation result

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Make sure the field exists in the data
            field_exists = False
            for col in data.columns:
                if col.name.lower() == rule.field_name.lower():
                    field_exists = True
                    break

            if not field_exists:
                raise ValidationError(
                    message=f"Field '{rule.field_name}' not found in the query results",
                    details={"available_fields": [col.name for col in data.columns]}
                )

            # Apply the validator
            validator = self._validators.get(rule.rule_type)
            if not validator:
                raise ValidationError(
                    message=f"No validator available for rule type: {rule.rule_type}",
                    details={}
                )

            total_records = len(data.records)
            failures = []

            # Apply the validation to each record
            for i, record in enumerate(data.records):
                # Get the field value
                field_value = None
                for field_name, value in record.items():
                    if field_name.lower() == rule.field_name.lower():
                        field_value = value
                        break

                # Validate the value
                try:
                    is_valid = validator(field_value, rule.parameters)
                    if not is_valid:
                        failures.append({
                            "row": i,
                            "field": rule.field_name,
                            "value": field_value,
                            "error": rule.error_message
                        })
                except Exception as e:
                    failures.append({
                        "row": i,
                        "field": rule.field_name,
                        "value": field_value,
                        "error": f"Validation error: {str(e)}"
                    })

            # Create the validation result
            validation_result = ValidationResult(
                rule_id=rule.id,
                table_name=rule.table_name,
                field_name=rule.field_name,
                validated_at=datetime.datetime.now(),
                success=len(failures) == 0,
                failures=failures,
                total_records=total_records,
                failed_records=len(failures)
            )

            # Save the result if a validation connection is configured
            if self._validation_connection_id:
                await self._save_validation_result(validation_result)

            return validation_result

        except Exception as e:
            if isinstance(e, ValidationError):
                raise

            self._logger.error(f"Validation error: {str(e)}")
            raise ValidationError(
                message=f"Failed to validate data: {str(e)}",
                details={"original_error": str(e)}
            )

    async def validate_all_rules(
            self,
            connection_id: str,
            table_name: str,
            data: QueryResult
    ) -> List[ValidationResult]:
        """
        Validate data against all active rules for a table.

        Args:
            connection_id: Connection ID
            table_name: Table name
            data: Query result to validate

        Returns:
            List of validation results

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Get all active rules for this table
            rules = await self.get_all_rules(
                connection_id=connection_id,
                table_name=table_name
            )

            active_rules = [rule for rule in rules if rule.active]

            if not active_rules:
                return []

            # Validate against each rule
            results = []
            for rule in active_rules:
                try:
                    result = await self.validate_data(rule, data)
                    results.append(result)
                except Exception as e:
                    self._logger.error(
                        f"Error validating rule {rule.id}: {str(e)}"
                    )

            return results

        except Exception as e:
            self._logger.error(f"Validation error: {str(e)}")
            raise ValidationError(
                message=f"Failed to validate data: {str(e)}",
                details={"original_error": str(e)}
            )

    async def get_validation_results(
            self,
            rule_id: Optional[str] = None,
            limit: int = 100
    ) -> List[ValidationResult]:
        """
        Get validation results, optionally filtered by rule.

        Args:
            rule_id: Optional rule ID to filter by
            limit: Maximum number of results to return

        Returns:
            List of validation results

        Raises:
            DatabaseError: If fetching results fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Build the SQL query
            if rule_id:
                sql = """
                      SELECT * \
                      FROM db_validation_results
                      WHERE rule_id = :rule_id
                      ORDER BY validated_at DESC LIMIT :limit \
                      """
                params = {"rule_id": rule_id, "limit": limit}
            else:
                sql = """
                      SELECT * \
                      FROM db_validation_results
                      ORDER BY validated_at DESC LIMIT :limit \
                      """
                params = {"limit": limit}

            # Execute the query
            results = await self._db_manager.execute_raw(
                sql=sql,
                params=params,
                connection_name=self._validation_connection_id
            )

            # Convert to ValidationResult objects
            validation_results: List[ValidationResult] = []
            for row in results:
                result_dict = {
                    "id": row["id"],
                    "rule_id": row["rule_id"],
                    "table_name": row["table_name"],
                    "field_name": row["field_name"],
                    "validated_at": row["validated_at"],
                    "success": row["success"],
                    "failures": json.loads(row["failures"]) if row["failures"] else [],
                    "total_records": row["total_records"],
                    "failed_records": row["failed_records"]
                }
                validation_results.append(ValidationResult(**result_dict))

            return validation_results

        except Exception as e:
            self._logger.error(f"Failed to get validation results: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get validation results: {str(e)}",
                details={"original_error": str(e)}
            )

    async def _save_validation_result(
            self,
            result: ValidationResult
    ) -> None:
        """
        Save a validation result to the database.

        Args:
            result: Validation result to save

        Raises:
            DatabaseError: If saving the result fails
        """
        try:
            # Insert the result into the database
            insert_sql = """
                         INSERT INTO db_validation_results (id, rule_id, table_name, field_name, validated_at, \
                                                            success, failures, total_records, failed_records) \
                         VALUES (:id, :rule_id, :table_name, :field_name, :validated_at, \
                                 :success, :failures, :total_records, :failed_records) \
                         """

            # Convert failures to JSON
            result_dict = result.dict()
            result_dict["failures"] = json.dumps(result_dict["failures"])

            await self._db_manager.execute_raw(
                sql=insert_sql,
                params=result_dict,
                connection_name=self._validation_connection_id
            )

        except Exception as e:
            self._logger.error(f"Failed to save validation result: {str(e)}")
            # Don't raise an exception here, just log it

    # Validation functions

    def _validate_range(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        Validate that a value is within a specified range.

        Args:
            value: Value to validate
            parameters: Dict with min and max values

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False

        try:
            # Convert to numeric if needed
            if not isinstance(value, (int, float)):
                value = float(value)

            min_val = parameters.get("min")
            max_val = parameters.get("max")

            # Check minimum if specified
            if min_val is not None:
                if value < min_val:
                    return False

            # Check maximum if specified
            if max_val is not None:
                if value > max_val:
                    return False

            return True

        except (ValueError, TypeError):
            # Value cannot be converted to a number
            return False

    def _validate_pattern(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        Validate that a value matches a regex pattern.

        Args:
            value: Value to validate
            parameters: Dict with pattern

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False

        pattern = parameters.get("pattern")
        if not pattern:
            return False

        try:
            # Convert to string if needed
            str_value = str(value)

            # Apply the regex pattern
            regex = re.compile(pattern)
            return bool(regex.match(str_value))

        except (TypeError, re.error):
            # Value cannot be converted or regex is invalid
            return False

    def _validate_not_null(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        Validate that a value is not null/None.

        Args:
            value: Value to validate
            parameters: Not used

        Returns:
            True if valid, False otherwise
        """
        return value is not None

    def _validate_unique(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        This validator is a placeholder as uniqueness needs to be
        checked across the entire dataset, not just one value.

        Args:
            value: Value to validate
            parameters: Dict with unique_values

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False

        # This needs to be pre-calculated across the whole dataset
        unique_values = parameters.get("unique_values", {})
        if not unique_values:
            return True

        # Convert the value to a string for comparison
        str_value = str(value)

        # Check if this value has been seen more than once
        return unique_values.get(str_value, 0) <= 1

    def _validate_length(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        Validate that a value's length is within specified bounds.

        Args:
            value: Value to validate
            parameters: Dict with min_length and max_length

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False

        try:
            # Convert to string if needed
            str_value = str(value)
            length = len(str_value)

            min_length = parameters.get("min_length")
            max_length = parameters.get("max_length")

            # Check minimum if specified
            if min_length is not None:
                if length < min_length:
                    return False

            # Check maximum if specified
            if max_length is not None:
                if length > max_length:
                    return False

            return True

        except TypeError:
            # Value cannot be converted to a string
            return False

    def _validate_reference(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        Validate that a value exists in a reference set.

        Args:
            value: Value to validate
            parameters: Dict with reference_values

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False

        reference_values = parameters.get("reference_values", [])
        if not reference_values:
            return False

        # Convert the value to a string for comparison
        str_value = str(value)

        # Check if this value exists in the reference set
        return str_value in [str(v) for v in reference_values]

    def _validate_enumeration(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        Validate that a value is one of a list of allowed values.

        Args:
            value: Value to validate
            parameters: Dict with allowed_values

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False

        allowed_values = parameters.get("allowed_values", [])
        if not allowed_values:
            return False

        # Convert the value and allowed values to strings for comparison
        str_value = str(value)
        allowed_str_values = [str(v) for v in allowed_values]

        return str_value in allowed_str_values

    def _validate_custom(
            self,
            value: Any,
            parameters: Dict[str, Any]
    ) -> bool:
        """
        Validate using a custom expression.

        Args:
            value: Value to validate
            parameters: Dict with expression

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return False

        expression = parameters.get("expression")
        if not expression:
            return False

        try:
            # Create a safe local environment for evaluation
            local_vars = {"value": value}

            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, local_vars)

            # Convert to boolean
            return bool(result)

        except Exception:
            # Expression evaluation failed
            return False


# Utility functions for creating validation rules

def create_range_rule(
        connection_id: str,
        table_name: str,
        field_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        error_message: Optional[str] = None
) -> ValidationRule:
    """
    Create a range validation rule.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_name: Field name
        name: Rule name (defaults to "Range check for {field_name}")
        description: Rule description
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        error_message: Error message (defaults to "Value must be between {min} and {max}")

    Returns:
        ValidationRule object
    """
    if name is None:
        if min_value is not None and max_value is not None:
            name = f"Range check for {field_name} ({min_value} to {max_value})"
        elif min_value is not None:
            name = f"Minimum value check for {field_name} (>= {min_value})"
        elif max_value is not None:
            name = f"Maximum value check for {field_name} (<= {max_value})"
        else:
            name = f"Range check for {field_name}"

    if error_message is None:
        if min_value is not None and max_value is not None:
            error_message = f"Value must be between {min_value} and {max_value}"
        elif min_value is not None:
            error_message = f"Value must be at least {min_value}"
        elif max_value is not None:
            error_message = f"Value must be at most {max_value}"
        else:
            error_message = "Value is outside the allowed range"

    parameters = {}
    if min_value is not None:
        parameters["min"] = min_value
    if max_value is not None:
        parameters["max"] = max_value

    return ValidationRule(
        name=name,
        description=description,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        rule_type=ValidationRuleType.RANGE,
        parameters=parameters,
        error_message=error_message
    )


def create_pattern_rule(
        connection_id: str,
        table_name: str,
        field_name: str,
        pattern: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> ValidationRule:
    """
    Create a pattern validation rule.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_name: Field name
        pattern: Regex pattern
        name: Rule name (defaults to "Pattern check for {field_name}")
        description: Rule description
        error_message: Error message (defaults to "Value must match pattern: {pattern}")

    Returns:
        ValidationRule object
    """
    if name is None:
        name = f"Pattern check for {field_name}"

    if error_message is None:
        error_message = f"Value must match pattern: {pattern}"

    parameters = {"pattern": pattern}

    return ValidationRule(
        name=name,
        description=description,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        rule_type=ValidationRuleType.PATTERN,
        parameters=parameters,
        error_message=error_message
    )


def create_not_null_rule(
        connection_id: str,
        table_name: str,
        field_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> ValidationRule:
    """
    Create a not-null validation rule.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_name: Field name
        name: Rule name (defaults to "Not null check for {field_name}")
        description: Rule description
        error_message: Error message (defaults to "Value cannot be null")

    Returns:
        ValidationRule object
    """
    if name is None:
        name = f"Not null check for {field_name}"

    if error_message is None:
        error_message = "Value cannot be null"

    parameters = {}

    return ValidationRule(
        name=name,
        description=description,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        rule_type=ValidationRuleType.NOT_NULL,
        parameters=parameters,
        error_message=error_message
    )


def create_unique_rule(
        connection_id: str,
        table_name: str,
        field_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> ValidationRule:
    """
    Create a uniqueness validation rule.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_name: Field name
        name: Rule name (defaults to "Uniqueness check for {field_name}")
        description: Rule description
        error_message: Error message (defaults to "Value must be unique")

    Returns:
        ValidationRule object
    """
    if name is None:
        name = f"Uniqueness check for {field_name}"

    if error_message is None:
        error_message = "Value must be unique"

    parameters = {}

    return ValidationRule(
        name=name,
        description=description,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        rule_type=ValidationRuleType.UNIQUE,
        parameters=parameters,
        error_message=error_message
    )


def create_length_rule(
        connection_id: str,
        table_name: str,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> ValidationRule:
    """
    Create a length validation rule.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_name: Field name
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        name: Rule name (defaults to "Length check for {field_name}")
        description: Rule description
        error_message: Error message (defaults to "Length must be between {min} and {max}")

    Returns:
        ValidationRule object
    """
    if name is None:
        if min_length is not None and max_length is not None:
            name = f"Length check for {field_name} ({min_length} to {max_length})"
        elif min_length is not None:
            name = f"Minimum length check for {field_name} (>= {min_length})"
        elif max_length is not None:
            name = f"Maximum length check for {field_name} (<= {max_length})"
        else:
            name = f"Length check for {field_name}"

    if error_message is None:
        if min_length is not None and max_length is not None:
            error_message = f"Length must be between {min_length} and {max_length}"
        elif min_length is not None:
            error_message = f"Length must be at least {min_length}"
        elif max_length is not None:
            error_message = f"Length must be at most {max_length}"
        else:
            error_message = "Length is outside the allowed range"

    parameters = {}
    if min_length is not None:
        parameters["min_length"] = min_length
    if max_length is not None:
        parameters["max_length"] = max_length

    return ValidationRule(
        name=name,
        description=description,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        rule_type=ValidationRuleType.LENGTH,
        parameters=parameters,
        error_message=error_message
    )


def create_enumeration_rule(
        connection_id: str,
        table_name: str,
        field_name: str,
        allowed_values: List[Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> ValidationRule:
    """
    Create an enumeration validation rule.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_name: Field name
        allowed_values: List of allowed values
        name: Rule name (defaults to "Enumeration check for {field_name}")
        description: Rule description
        error_message: Error message (defaults to "Value must be one of: {values}")

    Returns:
        ValidationRule object
    """
    if name is None:
        name = f"Enumeration check for {field_name}"

    if error_message is None:
        values_str = ", ".join([str(v) for v in allowed_values])
        error_message = f"Value must be one of: {values_str}"

    parameters = {"allowed_values": allowed_values}

    return ValidationRule(
        name=name,
        description=description,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        rule_type=ValidationRuleType.ENUMERATION,
        parameters=parameters,
        error_message=error_message
    )


def create_custom_rule(
        connection_id: str,
        table_name: str,
        field_name: str,
        expression: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> ValidationRule:
    """
    Create a custom validation rule.

    Args:
        connection_id: Database connection ID
        table_name: Table name
        field_name: Field name
        expression: Python expression that evaluates to a boolean
        name: Rule name (defaults to "Custom check for {field_name}")
        description: Rule description
        error_message: Error message (defaults to "Value failed custom validation")

    Returns:
        ValidationRule object
    """
    if name is None:
        name = f"Custom check for {field_name}"

    if error_message is None:
        error_message = "Value failed custom validation"

    parameters = {"expression": expression}

    return ValidationRule(
        name=name,
        description=description,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        rule_type=ValidationRuleType.CUSTOM,
        parameters=parameters,
        error_message=error_message
    )