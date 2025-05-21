from __future__ import annotations

"""
Validation utilities for the Database Manager.

This module provides functionality for validating database data according to
user-defined rules, enabling data quality checks and verification.
"""

import asyncio
import datetime
import json
import re
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast, Callable

from sqlalchemy import text

from qorzen.utils.exceptions import DatabaseError, ValidationError


class ValidationRuleType(str, Enum):
    """Types of validation rules."""

    RANGE = "range"
    PATTERN = "pattern"
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    LENGTH = "length"
    REFERENCE = "reference"
    ENUMERATION = "enumeration"
    CUSTOM = "custom"


class ValidationEngine:
    """Engine for data validation operations."""

    def __init__(
            self,
            database_manager: Any,
            logger: Any,
            validation_connection_id: Optional[str] = None
    ) -> None:
        """Initialize the validation engine.

        Args:
            database_manager: The database manager instance
            logger: Logger instance
            validation_connection_id: Connection ID for storing validation data
        """
        self._db_manager = database_manager
        self._logger = logger
        self._validation_connection_id = validation_connection_id
        self._validators = self._create_validators()
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the validation engine.

        This creates necessary tables for storing validation rules and results.

        Raises:
            DatabaseError: If initialization fails
        """
        if not self._validation_connection_id:
            self._logger.warning("No validation database connection configured")
            return

        try:
            await self._create_validation_tables()
            self._is_initialized = True
            self._logger.info("Validation engine initialized")

        except Exception as e:
            self._logger.error(f"Failed to initialize validation engine: {str(e)}")
            raise DatabaseError(
                message=f"Failed to initialize validation engine: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def _create_validation_tables(self) -> None:
        """Create necessary tables for validation.

        Raises:
            DatabaseError: If table creation fails
        """
        statements = [
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

        max_retries = 3

        for attempt in range(max_retries):
            try:
                async with self._db_manager.async_session(self._validation_connection_id) as session:
                    for stmt in statements:
                        self._logger.debug(f"Creating validation table: {stmt[:100]}...")
                        await session.execute(text(stmt))

                self._logger.debug("Validation tables created or already exist")
                return

            except Exception as e:
                self._logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")

                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    self._logger.error(
                        f"Failed to create validation tables after {max_retries} attempts: {str(e)}"
                    )
                    raise DatabaseError(
                        message=f"Failed to create validation tables: {str(e)}",
                        details={"original_error": str(e)}
                    ) from e

    def _create_validators(self) -> Dict[ValidationRuleType, Callable[[Any, Dict[str, Any]], bool]]:
        """Create validator functions for different rule types.

        Returns:
            Dict[ValidationRuleType, Callable]: Dictionary of validator functions
        """
        return {
            ValidationRuleType.RANGE: self._validate_range,
            ValidationRuleType.PATTERN: self._validate_pattern,
            ValidationRuleType.NOT_NULL: self._validate_not_null,
            ValidationRuleType.UNIQUE: self._validate_unique,
            ValidationRuleType.LENGTH: self._validate_length,
            ValidationRuleType.REFERENCE: self._validate_reference,
            ValidationRuleType.ENUMERATION: self._validate_enumeration,
            ValidationRuleType.CUSTOM: self._validate_custom
        }

    async def create_rule(
            self,
            rule_type: str,
            connection_id: str,
            table_name: str,
            field_name: str,
            parameters: Dict[str, Any],
            error_message: str,
            name: Optional[str] = None,
            description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a validation rule.

        Args:
            rule_type: Type of validation rule
            connection_id: The connection ID
            table_name: The table name
            field_name: The field name
            parameters: Rule parameters
            error_message: Error message when validation fails
            name: Optional rule name
            description: Optional description

        Returns:
            Dict[str, Any]: The created rule

        Raises:
            DatabaseError: If rule creation fails
            ValueError: If rule parameters are invalid
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Validate rule type
            try:
                rule_type_enum = ValidationRuleType(rule_type)
            except ValueError:
                raise ValueError(f"Invalid rule type: {rule_type}")

            # Generate default name if not provided
            if name is None:
                name = f"{rule_type.capitalize()} check for {field_name}"

            # Generate a rule ID
            rule_id = str(uuid.uuid4())
            now = datetime.datetime.now()

            # Validate parameters based on rule type
            self._validate_rule_parameters(rule_type_enum, parameters)

            rule = {
                "id": rule_id,
                "name": name,
                "description": description,
                "connection_id": connection_id,
                "table_name": table_name,
                "field_name": field_name,
                "rule_type": rule_type,
                "parameters": json.dumps(parameters),
                "error_message": error_message,
                "active": True,
                "created_at": now,
                "updated_at": now
            }

            insert_sql = """
                         INSERT INTO db_validation_rules
                         (id, name, description, connection_id, table_name, field_name,
                          rule_type, parameters, error_message, active, created_at, updated_at)
                         VALUES (:id, :name, :description, :connection_id, :table_name, :field_name, \
                                 :rule_type, :parameters, :error_message, :active, :created_at, :updated_at) \
                         """

            async with self._db_manager.async_session(self._validation_connection_id) as session:
                await session.execute(text(insert_sql), rule)

            self._logger.info(f"Created validation rule: {name}")

            # Convert parameters back from JSON string
            rule["parameters"] = parameters

            return rule

        except Exception as e:
            self._logger.error(f"Failed to create validation rule: {str(e)}")

            if isinstance(e, ValueError):
                raise

            raise DatabaseError(
                message=f"Failed to create validation rule: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def update_rule(
            self,
            rule_id: str,
            **updates: Any
    ) -> Dict[str, Any]:
        """Update a validation rule.

        Args:
            rule_id: The rule ID
            **updates: Fields to update

        Returns:
            Dict[str, Any]: The updated rule

        Raises:
            DatabaseError: If rule update fails
            ValueError: If rule parameters are invalid
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            # Get existing rule
            existing_rule = await self.get_rule(rule_id)
            if not existing_rule:
                raise DatabaseError(
                    message=f"Validation rule not found: {rule_id}",
                    details={}
                )

            # Update fields
            rule = dict(existing_rule)
            parameters_updated = False

            for key, value in updates.items():
                if key in rule:
                    if key == "parameters":
                        parameters_updated = True
                        rule[key] = value
                    else:
                        rule[key] = value

            # Update timestamp
            rule["updated_at"] = datetime.datetime.now()

            # Validate parameters if updated
            if parameters_updated:
                self._validate_rule_parameters(ValidationRuleType(rule["rule_type"]), rule["parameters"])
                # Convert parameters to JSON for storage
                rule["parameters"] = json.dumps(rule["parameters"])

            update_sql = """
                         UPDATE db_validation_rules
                         SET name          = :name,
                             description   = :description,
                             connection_id = :connection_id,
                             table_name    = :table_name,
                             field_name    = :field_name,
                             rule_type     = :rule_type,
                             parameters    = :parameters,
                             error_message = :error_message,
                             active        = :active,
                             updated_at    = :updated_at
                         WHERE id = :id \
                         """

            async with self._db_manager.async_session(self._validation_connection_id) as session:
                await session.execute(text(update_sql), rule)

            self._logger.info(f"Updated validation rule: {rule['name']}")

            # Convert parameters back from JSON string if it was stored as JSON
            if isinstance(rule["parameters"], str):
                rule["parameters"] = json.loads(rule["parameters"])

            return rule

        except Exception as e:
            self._logger.error(f"Failed to update validation rule: {str(e)}")

            if isinstance(e, ValueError):
                raise

            raise DatabaseError(
                message=f"Failed to update validation rule: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def delete_rule(self, rule_id: str) -> bool:
        """Delete a validation rule.

        Args:
            rule_id: The rule ID

        Returns:
            bool: True if successful

        Raises:
            DatabaseError: If rule deletion fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            delete_sql = "DELETE FROM db_validation_rules WHERE id = :id"

            async with self._db_manager.async_session(self._validation_connection_id) as session:
                await session.execute(text(delete_sql), {"id": rule_id})

            self._logger.info(f"Deleted validation rule: {rule_id}")
            return True

        except Exception as e:
            self._logger.error(f"Failed to delete validation rule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to delete validation rule: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def get_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Get a validation rule.

        Args:
            rule_id: The rule ID

        Returns:
            Optional[Dict[str, Any]]: The rule, or None if not found

        Raises:
            DatabaseError: If getting rule fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            sql = "SELECT * FROM db_validation_rules WHERE id = :id"

            async with self._db_manager.async_session(self._validation_connection_id) as session:
                result = await session.execute(text(sql), {"id": rule_id})
                row = result.fetchone()

            if not row:
                return None

            rule = {
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "connection_id": row[3],
                "table_name": row[4],
                "field_name": row[5],
                "rule_type": row[6],
                "parameters": json.loads(row[7]),
                "error_message": row[8],
                "active": row[9],
                "created_at": row[10],
                "updated_at": row[11]
            }

            return rule

        except Exception as e:
            self._logger.error(f"Failed to get validation rule: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get validation rule: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def get_all_rules(
            self,
            connection_id: Optional[str] = None,
            table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all validation rules, optionally filtered.

        Args:
            connection_id: The connection ID to filter by
            table_name: The table name to filter by

        Returns:
            List[Dict[str, Any]]: List of validation rules

        Raises:
            DatabaseError: If getting rules fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
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

            async with self._db_manager.async_session(self._validation_connection_id) as session:
                result = await session.execute(text(sql), params)
                rows = result.fetchall()

            rules = []
            for row in rows:
                rule = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "connection_id": row[3],
                    "table_name": row[4],
                    "field_name": row[5],
                    "rule_type": row[6],
                    "parameters": json.loads(row[7]),
                    "error_message": row[8],
                    "active": row[9],
                    "created_at": row[10],
                    "updated_at": row[11]
                }
                rules.append(rule)

            return rules

        except Exception as e:
            self._logger.error(f"Failed to get validation rules: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get validation rules: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def validate_data(
            self,
            rule: Dict[str, Any],
            data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate data against a rule.

        Args:
            rule: The validation rule
            data: The data to validate

        Returns:
            Dict[str, Any]: Validation result

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Check if field exists in data
            records = data.get("records", [])
            columns = data.get("columns", [])

            field_exists = False
            for col in columns:
                if col["name"].lower() == rule["field_name"].lower():
                    field_exists = True
                    break

            if not field_exists:
                raise ValidationError(
                    message=f"Field '{rule['field_name']}' not found in the query results",
                    details={"available_fields": [col["name"] for col in columns]}
                )

            # Get validator function for rule type
            rule_type = ValidationRuleType(rule["rule_type"])
            validator = self._validators.get(rule_type)

            if not validator:
                raise ValidationError(
                    message=f"No validator available for rule type: {rule_type}",
                    details={}
                )

            # Validate data
            total_records = len(records)
            failures = []

            for i, record in enumerate(records):
                field_value = None

                for field_name, value in record.items():
                    if field_name.lower() == rule["field_name"].lower():
                        field_value = value
                        break

                try:
                    is_valid = validator(field_value, rule["parameters"])

                    if not is_valid:
                        failures.append({
                            "row": i,
                            "field": rule["field_name"],
                            "value": field_value,
                            "error": rule["error_message"]
                        })
                except Exception as e:
                    failures.append({
                        "row": i,
                        "field": rule["field_name"],
                        "value": field_value,
                        "error": f"Validation error: {str(e)}"
                    })

            # Create validation result
            validation_result = {
                "id": str(uuid.uuid4()),
                "rule_id": rule["id"],
                "table_name": rule["table_name"],
                "field_name": rule["field_name"],
                "validated_at": datetime.datetime.now(),
                "success": len(failures) == 0,
                "failures": failures,
                "total_records": total_records,
                "failed_records": len(failures)
            }

            # Save validation result
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
            ) from e

    async def validate_all_rules(
            self,
            connection_id: str,
            table_name: str,
            data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate data against all rules for a table.

        Args:
            connection_id: The connection ID
            table_name: The table name
            data: The data to validate

        Returns:
            List[Dict[str, Any]]: Validation results

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Get all active rules for the table
            rules = await self.get_all_rules(connection_id=connection_id, table_name=table_name)
            active_rules = [rule for rule in rules if rule["active"]]

            if not active_rules:
                return []

            # Validate data against each rule
            results = []

            for rule in active_rules:
                try:
                    result = await self.validate_data(rule, data)
                    results.append(result)
                except Exception as e:
                    self._logger.error(f"Error validating rule {rule['id']}: {str(e)}")

            return results

        except Exception as e:
            self._logger.error(f"Validation error: {str(e)}")
            raise ValidationError(
                message=f"Failed to validate data: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def get_validation_results(
            self,
            rule_id: Optional[str] = None,
            limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get validation results, optionally filtered by rule ID.

        Args:
            rule_id: Optional rule ID to filter by
            limit: Maximum number of results to return

        Returns:
            List[Dict[str, Any]]: List of validation results

        Raises:
            DatabaseError: If getting results fails
        """
        if not self._validation_connection_id:
            raise DatabaseError(
                message="No validation database connection configured",
                details={}
            )

        try:
            if rule_id:
                sql = """
                      SELECT *
                      FROM db_validation_results
                      WHERE rule_id = :rule_id
                      ORDER BY validated_at DESC LIMIT :limit \
                      """
                params = {"rule_id": rule_id, "limit": limit}
            else:
                sql = """
                      SELECT *
                      FROM db_validation_results
                      ORDER BY validated_at DESC LIMIT :limit \
                      """
                params = {"limit": limit}

            async with self._db_manager.async_session(self._validation_connection_id) as session:
                result = await session.execute(text(sql), params)
                rows = result.fetchall()

            validation_results = []

            for row in rows:
                result_dict = {
                    "id": row[0],
                    "rule_id": row[1],
                    "table_name": row[2],
                    "field_name": row[3],
                    "validated_at": row[4],
                    "success": row[5],
                    "failures": json.loads(row[6]) if row[6] else [],
                    "total_records": row[7],
                    "failed_records": row[8]
                }
                validation_results.append(result_dict)

            return validation_results

        except Exception as e:
            self._logger.error(f"Failed to get validation results: {str(e)}")
            raise DatabaseError(
                message=f"Failed to get validation results: {str(e)}",
                details={"original_error": str(e)}
            ) from e

    async def _save_validation_result(self, result: Dict[str, Any]) -> None:
        """Save a validation result.

        Args:
            result: The validation result

        Raises:
            DatabaseError: If saving result fails
        """
        try:
            insert_sql = """
                         INSERT INTO db_validation_results
                         (id, rule_id, table_name, field_name, validated_at,
                          success, failures, total_records, failed_records)
                         VALUES (:id, :rule_id, :table_name, :field_name, :validated_at, \
                                 :success, :failures, :total_records, :failed_records) \
                         """

            # Convert failures to JSON
            result_dict = dict(result)
            result_dict["failures"] = json.dumps(result_dict["failures"])

            async with self._db_manager.async_session(self._validation_connection_id) as session:
                await session.execute(text(insert_sql), result_dict)

        except Exception as e:
            self._logger.error(f"Failed to save validation result: {str(e)}")

    def _validate_rule_parameters(
            self,
            rule_type: ValidationRuleType,
            parameters: Dict[str, Any]
    ) -> None:
        """Validate parameters for a rule type.

        Args:
            rule_type: The rule type
            parameters: The parameters

        Raises:
            ValueError: If parameters are invalid
        """
        if rule_type == ValidationRuleType.RANGE:
            has_min = "min" in parameters
            has_max = "max" in parameters

            if not has_min and not has_max:
                raise ValueError("Range rule must have min or max parameter")

        elif rule_type == ValidationRuleType.PATTERN:
            if "pattern" not in parameters or not parameters["pattern"]:
                raise ValueError("Pattern rule must have pattern parameter")

            try:
                re.compile(parameters["pattern"])
            except re.error as e:
                raise ValueError(f"Invalid regular expression: {str(e)}")

        elif rule_type == ValidationRuleType.LENGTH:
            has_min = "min_length" in parameters
            has_max = "max_length" in parameters

            if not has_min and not has_max:
                raise ValueError("Length rule must have min_length or max_length parameter")

        elif rule_type == ValidationRuleType.ENUMERATION:
            if "allowed_values" not in parameters or not parameters["allowed_values"]:
                raise ValueError("Enumeration rule must have allowed_values parameter")

        elif rule_type == ValidationRuleType.REFERENCE:
            if "reference_values" not in parameters or not parameters["reference_values"]:
                raise ValueError("Reference rule must have reference_values parameter")

        elif rule_type == ValidationRuleType.CUSTOM:
            if "expression" not in parameters or not parameters["expression"]:
                raise ValueError("Custom rule must have expression parameter")

    def _validate_range(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against a range rule.

        Args:
            value: The value to validate
            parameters: Range parameters (min, max)

        Returns:
            bool: True if valid
        """
        if value is None:
            return False

        try:
            if not isinstance(value, (int, float)):
                value = float(value)

            min_val = parameters.get("min")
            max_val = parameters.get("max")

            if min_val is not None:
                if value < min_val:
                    return False

            if max_val is not None:
                if value > max_val:
                    return False

            return True

        except (ValueError, TypeError):
            return False

    def _validate_pattern(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against a pattern rule.

        Args:
            value: The value to validate
            parameters: Pattern parameters (pattern)

        Returns:
            bool: True if valid
        """
        if value is None:
            return False

        pattern = parameters.get("pattern")
        if not pattern:
            return False

        try:
            str_value = str(value)
            regex = re.compile(pattern)
            return bool(regex.match(str_value))
        except (TypeError, re.error):
            return False

    def _validate_not_null(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against a not-null rule.

        Args:
            value: The value to validate
            parameters: Not used

        Returns:
            bool: True if valid
        """
        return value is not None

    def _validate_unique(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against a uniqueness rule.

        Args:
            value: The value to validate
            parameters: Uniqueness parameters (unique_values)

        Returns:
            bool: True if valid
        """
        if value is None:
            return False

        unique_values = parameters.get("unique_values", {})
        if not unique_values:
            return True

        str_value = str(value)
        return unique_values.get(str_value, 0) <= 1

    def _validate_length(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against a length rule.

        Args:
            value: The value to validate
            parameters: Length parameters (min_length, max_length)

        Returns:
            bool: True if valid
        """
        if value is None:
            return False

        try:
            str_value = str(value)
            length = len(str_value)

            min_length = parameters.get("min_length")
            max_length = parameters.get("max_length")

            if min_length is not None:
                if length < min_length:
                    return False

            if max_length is not None:
                if length > max_length:
                    return False

            return True

        except TypeError:
            return False

    def _validate_reference(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against a reference rule.

        Args:
            value: The value to validate
            parameters: Reference parameters (reference_values)

        Returns:
            bool: True if valid
        """
        if value is None:
            return False

        reference_values = parameters.get("reference_values", [])
        if not reference_values:
            return False

        str_value = str(value)
        return str_value in [str(v) for v in reference_values]

    def _validate_enumeration(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against an enumeration rule.

        Args:
            value: The value to validate
            parameters: Enumeration parameters (allowed_values)

        Returns:
            bool: True if valid
        """
        if value is None:
            return False

        allowed_values = parameters.get("allowed_values", [])
        if not allowed_values:
            return False

        str_value = str(value)
        allowed_str_values = [str(v) for v in allowed_values]

        return str_value in allowed_str_values

    def _validate_custom(self, value: Any, parameters: Dict[str, Any]) -> bool:
        """Validate a value against a custom rule.

        Args:
            value: The value to validate
            parameters: Custom parameters (expression)

        Returns:
            bool: True if valid
        """
        if value is None:
            return False

        expression = parameters.get("expression")
        if not expression:
            return False

        try:
            local_vars = {"value": value}
            result = eval(expression, {"__builtins__": {}}, local_vars)
            return bool(result)
        except Exception:
            return False

    async def shutdown(self) -> None:
        """Shut down the validation engine."""
        self._is_initialized = False
        self._logger.info("Validation engine shut down")


# Helper functions for creating common validation rule types

async def create_range_rule(
        validation_engine: ValidationEngine,
        connection_id: str,
        table_name: str,
        field_name: str,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a range validation rule.

    Args:
        validation_engine: The validation engine
        connection_id: The connection ID
        table_name: The table name
        field_name: The field name
        min_value: Optional minimum value
        max_value: Optional maximum value
        name: Optional rule name
        description: Optional description
        error_message: Optional error message

    Returns:
        Dict[str, Any]: The created rule

    Raises:
        DatabaseError: If rule creation fails
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

    return await validation_engine.create_rule(
        rule_type=ValidationRuleType.RANGE,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        parameters=parameters,
        error_message=error_message,
        name=name,
        description=description
    )


async def create_pattern_rule(
        validation_engine: ValidationEngine,
        connection_id: str,
        table_name: str,
        field_name: str,
        pattern: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a pattern validation rule.

    Args:
        validation_engine: The validation engine
        connection_id: The connection ID
        table_name: The table name
        field_name: The field name
        pattern: Regular expression pattern
        name: Optional rule name
        description: Optional description
        error_message: Optional error message

    Returns:
        Dict[str, Any]: The created rule

    Raises:
        DatabaseError: If rule creation fails
    """
    if name is None:
        name = f"Pattern check for {field_name}"

    if error_message is None:
        error_message = f"Value must match pattern: {pattern}"

    parameters = {"pattern": pattern}

    return await validation_engine.create_rule(
        rule_type=ValidationRuleType.PATTERN,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        parameters=parameters,
        error_message=error_message,
        name=name,
        description=description
    )


async def create_not_null_rule(
        validation_engine: ValidationEngine,
        connection_id: str,
        table_name: str,
        field_name: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a not-null validation rule.

    Args:
        validation_engine: The validation engine
        connection_id: The connection ID
        table_name: The table name
        field_name: The field name
        name: Optional rule name
        description: Optional description
        error_message: Optional error message

    Returns:
        Dict[str, Any]: The created rule

    Raises:
        DatabaseError: If rule creation fails
    """
    if name is None:
        name = f"Not null check for {field_name}"

    if error_message is None:
        error_message = "Value cannot be null"

    parameters = {}

    return await validation_engine.create_rule(
        rule_type=ValidationRuleType.NOT_NULL,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        parameters=parameters,
        error_message=error_message,
        name=name,
        description=description
    )


async def create_length_rule(
        validation_engine: ValidationEngine,
        connection_id: str,
        table_name: str,
        field_name: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> Dict[str, Any]:
    """Create a length validation rule.

    Args:
        validation_engine: The validation engine
        connection_id: The connection ID
        table_name: The table name
        field_name: The field name
        min_length: Optional minimum length
        max_length: Optional maximum length
        name: Optional rule name
        description: Optional description
        error_message: Optional error message

    Returns:
        Dict[str, Any]: The created rule

    Raises:
        DatabaseError: If rule creation fails
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

    return await validation_engine.create_rule(
        rule_type=ValidationRuleType.LENGTH,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        parameters=parameters,
        error_message=error_message,
        name=name,
        description=description
    )


async def create_enumeration_rule(
        validation_engine: ValidationEngine,
        connection_id: str,
        table_name: str,
        field_name: str,
        allowed_values: List[Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
        error_message: Optional[str] = None
) -> Dict[str, Any]:
    """Create an enumeration validation rule.

    Args:
        validation_engine: The validation engine
        connection_id: The connection ID
        table_name: The table name
        field_name: The field name
        allowed_values: List of allowed values
        name: Optional rule name
        description: Optional description
        error_message: Optional error message

    Returns:
        Dict[str, Any]: The created rule

    Raises:
        DatabaseError: If rule creation fails
    """
    if name is None:
        name = f"Enumeration check for {field_name}"

    if error_message is None:
        values_str = ", ".join([str(v) for v in allowed_values])
        error_message = f"Value must be one of: {values_str}"

    parameters = {"allowed_values": allowed_values}

    return await validation_engine.create_rule(
        rule_type=ValidationRuleType.ENUMERATION,
        connection_id=connection_id,
        table_name=table_name,
        field_name=field_name,
        parameters=parameters,
        error_message=error_message,
        name=name,
        description=description
    )