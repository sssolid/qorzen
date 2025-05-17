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
│   ├── concurrency_manager.py
│   ├── config_manager.py
│   ├── database_manager.py
│   ├── dependency_manager.py
│   ├── error_handler.py
│   ├── event_bus_manager.py
│   ├── event_model.py
│   ├── file_manager.py
│   ├── logging_manager.py
│   ├── plugin_isolation_manager.py
│   ├── plugin_manager.py
│   ├── remote_manager.py
│   ├── resource_monitoring_manager.py
│   ├── security_manager.py
│   └── task_manager.py
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
│   ├── plugin_state_manager.py
│   ├── repository.py
│   ├── signing.py
│   ├── tools.py
│   └── ui_registry.py
├── plugins/
│   ├── application_launcher/
│   │   ├── code/
│   │   │   ├── __init__.py
│   │   │   ├── events.py
│   │   │   ├── plugin.py
│   │   │   ├── presets.py
│   │   │   └── process_utils.py
│   │   ├── __init__.py
│   │   └── manifest.json
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
│   ├── database_connector_plugin/
│   │   ├── code/
│   │   │   ├── connectors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── as400.py
│   │   │   │   ├── base.py
│   │   │   │   └── odbc.py
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connection_dialog.py
│   │   │   │   ├── main_tab.py
│   │   │   │   ├── mapping_dialog.py
│   │   │   │   ├── query_editor.py
│   │   │   │   └── results_view.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── history.py
│   │   │   │   ├── mapping.py
│   │   │   │   └── validation.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   └── plugin.py
│   │   ├── __init__.py
│   │   └── manifest.json
│   ├── sample_async_plugin/
│   │   ├── code/
│   │   │   ├── __init__.py
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
│   ├── logs.py
│   ├── main_window.py
│   ├── plugins.py
│   ├── task_monitor.py
│   ├── thread_safe_signaler.py
│   ├── ui_component.py
│   └── ui_integration.py
├── utils/
│   ├── __init__.py
│   ├── exceptions.py
│   ├── qt_thread_debug.py
│   └── qtasync.py
├── __init__.py
├── __main__.py
├── __version__.py
├── main.py
├── plugin_debug.py
└── resources_rc.py
```

[Back to Project Index](index.md)