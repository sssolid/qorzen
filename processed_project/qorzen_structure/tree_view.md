# Project Structure Tree View

Project: qorzen

```
qorzen/
├── core/
│   ├── __init__.py
│   ├── api_manager.py
│   ├── app.py
│   ├── base.py
│   ├── cloud_manager.py
│   ├── config_manager.py
│   ├── database_manager.py
│   ├── event_bus_manager.py
│   ├── event_model.py
│   ├── file_manager.py
│   ├── logging_manager.py
│   ├── monitoring_manager.py
│   ├── plugin_error_handler.py
│   ├── plugin_manager.py
│   ├── remote_manager.py
│   ├── security_manager.py
│   └── thread_manager.py
├── models/
│   ├── __init__.py
│   ├── audit.py
│   ├── base.py
│   ├── plugin.py
│   ├── system.py
│   └── user.py
├── plugin_system/
│   ├── __init__.py
│   ├── cli.py
│   ├── config_schema.py
│   ├── dependency.py
│   ├── extension.py
│   ├── installer.py
│   ├── integration.py
│   ├── interface.py
│   ├── lifecycle.py
│   ├── manifest.py
│   ├── package.py
│   ├── repository.py
│   ├── signing.py
│   └── tools.py
├── plugins/
│   ├── aces_validator/
│   │   └── __init__.py
│   ├── as400_connector_plugin/
│   │   ├── code/
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── as400_tab.py
│   │   │   │   ├── connection_dialog.py
│   │   │   │   ├── query_editor.py
│   │   │   │   ├── results_view.py
│   │   │   │   └── visualization.py
│   │   │   ├── __init__.py
│   │   │   ├── connector.py
│   │   │   ├── models.py
│   │   │   ├── plugin.py
│   │   │   └── utils.py
│   │   ├── queries/
│   │   │   ├── account_sales.sql
│   │   │   ├── popularity_codes.sql
│   │   │   └── table_descriptions.sql
│   │   └── __init__.py
│   ├── event_monitor_plugin/
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── example_plugin/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── hooks.py
│   │   │   └── plugin.py
│   │   ├── Manifest.json
│   │   ├── README.md
│   │   └── __init__.py
│   ├── system_monitor/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── hooks.py
│   │   │   └── plugin.py
│   │   ├── __init__.py
│   │   └── manifest.json
│   ├── vcdb_explorer/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── data_table.py
│   │   │   ├── database_handler.py
│   │   │   ├── events.py
│   │   │   ├── export.py
│   │   │   ├── filter_panel.py
│   │   │   ├── models.py
│   │   │   └── plugin.py
│   │   ├── resources/
│   │   │   ├── ui_icons/
│   │   │   │   ├── database-search.svg
│   │   │   │   ├── database.svg
│   │   │   │   └── library-books.svg
│   │   │   ├── initialdb.ico
│   │   │   ├── initialdb.png
│   │   │   ├── initialdb_1000.png
│   │   │   ├── logo.png
│   │   │   └── splash.png
│   │   ├── README.md
│   │   ├── __init__.py
│   │   └── manifest.json
│   └── __init__.py
├── ui/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── integration.py
│   ├── logs.py
│   ├── panel_ui.py
│   └── plugins.py
├── utils/
│   ├── __init__.py
│   └── exceptions.py
├── __init__.py
├── __main__.py
├── __version__.py
├── main.py
└── resources_rc.py
```

[Back to Project Index](index.md)