# Database Connector Plugin for Qorzen

The Database Connector Plugin provides robust connectivity to various database systems, including AS400/iSeries and ODBC-compatible databases. This plugin enables users to connect, query, and manage database interactions with powerful features like field mapping, data validation, and historical data tracking.

## Features

- **Multiple Database Support**: Connect to AS400/iSeries databases (via JT400) and ODBC data sources
- **Field Mapping**: Create standardized field mappings to normalize column names across databases
- **SQL Query Editor**: Write and execute SQL queries with syntax highlighting and parameter support
- **Data Validation**: Define and run validation rules to check data quality and consistency
- **Historical Data Tracking**: Schedule periodic data collection for historical reference
- **Import/Export**: Save queries, mappings, and results in various formats

## Requirements

- Qorzen framework v1.0.0 or higher
- Python 3.7+
- Required Python packages:
  - pydantic
  - pyodbc
  - jpype1 (for AS400 connections)
  - sqlparse (optional, for SQL formatting)

## Getting Started

1. Install the plugin through the Qorzen plugin manager
2. Create a new database connection in the Connection Manager
3. Create field mappings (optional)
4. Start querying your database using the Query Editor

## Documentation

For more information on using this plugin, please refer to the Qorzen documentation.