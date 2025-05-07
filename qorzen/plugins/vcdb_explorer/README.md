# VCdb Explorer Plugin

## Overview

VCdb Explorer is a Qorzen plugin that provides advanced query and exploration capabilities for the Vehicle Component Database (VCdb). The plugin allows users to:

- Create complex filter queries with multiple filter groups
- Build dynamic, cascading filters that update based on previous selections
- View query results in a customizable data table
- Sort and filter table data
- Export results to CSV or Excel formats

## Features

### Dynamic Filter Panels

- Each filter panel represents a set of conditions combined with AND logic
- Multiple filter panels are combined with OR logic
- Filter values automatically update based on previously selected filters
- Mandatory filters include Year, Year Range, Make, Model, and Submodel
- Additional filters can be added as needed

### Customizable Results Table

- Configurable columns with drag-and-drop reordering
- Sortable columns
- Filterable data with text search capabilities
- Pagination for large result sets
- Export to CSV and Excel formats

### Database Integration

- Connects to PostgreSQL databases with the VCdb schema
- Optimized queries for performance
- Support for large data sets with efficient pagination

## Installation

1. Ensure Qorzen core is installed
2. Install the VCdb Explorer plugin:
   ```
   qorzen-plugin install vcdb_explorer-1.0.0.zip
   ```
3. Configure database connection in Qorzen settings

## Configuration

The following configuration options are available:

### Database Connection

- `database.host`: PostgreSQL server hostname (default: "localhost")
- `database.port`: PostgreSQL server port (default: 5432)
- `database.name`: Database name (default: "vcdb")
- `database.user`: Database username (default: "postgres")
- `database.password`: Database password

### User Interface

- `ui.max_filter_panels`: Maximum number of filter panels allowed (default: 5)
- `ui.default_page_size`: Default number of rows per page (default: 100)

### Export Settings

- `export.max_rows`: Maximum number of rows allowed for export (default: 10000)

## Usage

### Creating Filter Queries

1. Add or remove filter panels using the "Add Filter Group" and "Remove Group" buttons
2. Each panel represents a set of conditions (AND logic)
3. Multiple panels are combined with OR logic
4. Add filters to each panel using the "Add Filter" button
5. Select filter values from the dropdowns
6. Click "Run Query" to execute the search

### Working with Results

1. Results appear in the data table below the filter panels
2. Click column headers to sort
3. Use the "Select Columns" button to customize visible columns
4. Filter table data using the "Add Filter" button in the table filters section
5. Navigate between pages using the pagination controls
6. Export data using the "Export CSV" or "Export Excel" buttons

## Dependencies

- Python 3.11+
- SQLAlchemy
- PySide6 (Qt)
- openpyxl (optional, for Excel export)

## Troubleshooting

### Database Connection Issues

- Verify database credentials in the plugin configuration
- Ensure the PostgreSQL server is running and accessible
- Check that the database contains the VCdb schema

### Performance Considerations

- Large filter sets may take longer to execute
- Consider using more specific filters to reduce result size
- Exporting very large datasets may be slow; use filters to reduce size

## License

This plugin is released under the MIT License.

## Support

For issues, feature requests, or questions, please contact the Qorzen support team.