# VCdb Explorer Plugin

A plugin for the Qorzen framework that provides a comprehensive interface for exploring and querying the Vehicle Component Database (VCdb).

## Overview

The VCdb Explorer plugin allows users to search, filter, and export vehicle data from the VCdb database using a user-friendly interface. It integrates with the Qorzen framework to leverage core services like database access, event handling, and threading.

## Key Features

- Multi-panel filtering system for complex vehicle queries
- Configurable data table with column selection
- CSV and Excel export capabilities
- Pagination for large result sets
- Table-level filtering for further refinement

## Architecture

The plugin follows a modular architecture that integrates with the Qorzen framework:

### Core Components

1. **Plugin Entry Point** (`plugin.py`): Handles initialization, integration with the UI, and lifecycle management
2. **Database Handler** (`database_handler.py`): Manages database operations through the core DatabaseManager
3. **Events System** (`events.py`): Defines plugin-specific event types
4. **UI Components**:
   - **Filter Panel** (`filter_panel.py`): Manages query filter panels
   - **Data Table** (`data_table.py`): Displays and manages query results
   - **Export** (`export.py`): Handles data export functionality

### Data Flow

1. User configures filters in the Filter Panel
2. Query is executed through the Database Handler
3. Results are displayed in the Data Table
4. Optional export of data to CSV or Excel

## Integration with Qorzen Framework

The plugin integrates with the following core Qorzen services:

- **DatabaseManager**: For database access and query execution
- **EventBusManager**: For event-driven communication between components
- **ThreadManager**: For executing long-running operations in background threads
- **LoggerManager**: For structured logging
- **ConfigManager**: For plugin configuration

## Plugin Events

Custom events used by the plugin:

- `filter_changed`: Emitted when a filter is changed
- `filters_refreshed`: Emitted when filters are refreshed
- `query_execute`: Emitted to request query execution
- `query_results`: Emitted when query results are available

## Configuration Options

The plugin supports the following configuration options:

```yaml
plugins:
  vcdb_explorer:
    database:
      host: localhost
      port: 5432
      name: vcdb
      user: postgres
      password: 
    ui:
      max_filter_panels: 5
      default_page_size: 100
    export:
      max_rows: 10000
```

## Requirements

- Python 3.11+
- PySide6
- SQLAlchemy
- openpyxl (optional, for Excel export)

## Files Structure

```
plugins/vcdb_explorer/
├── __init__.py             # Plugin package initialization
├── code/
│   ├── __init__.py         # Code package initialization
│   ├── database_handler.py # Database integration handler
│   ├── data_table.py       # Data table UI component
│   ├── events.py           # Plugin event definitions
│   ├── export.py           # Data export functionality
│   ├── filter_panel.py     # Filter panel UI component
│   ├── models.py           # Database model definitions
│   └── plugin.py           # Plugin main entry point
└── manifest.json           # Plugin manifest
```

## Development Guidelines

When extending or modifying this plugin:

1. Use proper type hints and follow PEP 8 standards
2. Leverage the provided event system for component communication
3. Utilize the core managers provided by the Qorzen framework
4. Handle errors gracefully with appropriate user feedback
5. Follow the established code organization pattern