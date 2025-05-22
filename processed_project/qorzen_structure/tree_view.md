# Project Structure Tree View

Project: qorzen

```
qorzen/
├── core/
│   ├── database/
│   │   ├── connectors/
│   │   │   ├── __init__.py
│   │   │   ├── as400.py
│   │   │   ├── base.py
│   │   │   ├── odbc.py
│   │   │   └── sqlite.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── field_mapper.py
│   │   │   ├── history_manager.py
│   │   │   └── validation_engine.py
│   │   └── __init__.py
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
│   ├── database_connector_plugin/
│   │   ├── code/
│   │   │   ├── services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── export_service.py
│   │   │   │   └── query_service.py
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connection_dialog.py
│   │   │   │   ├── field_mapping_tab.py
│   │   │   │   ├── history_tab.py
│   │   │   │   ├── main_tab.py
│   │   │   │   ├── main_widget.py
│   │   │   │   ├── query_dialog.py
│   │   │   │   ├── results_tab.py
│   │   │   │   └── validation_tab.py
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   └── plugin.py
│   │   ├── README.md
│   │   ├── __init__.py
│   │   └── manifest.json
│   ├── media_processor_plugin/
│   │   ├── code/
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── isnet_model.py
│   │   │   │   ├── modnet_model.py
│   │   │   │   ├── processing_config.py
│   │   │   │   └── u2net_model.py
│   │   │   ├── processors/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── batch_processor.py
│   │   │   │   ├── media_processor.py
│   │   │   │   └── optimized_processor.py
│   │   │   ├── ui/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_manager_dialog.py
│   │   │   │   ├── batch_dialog.py
│   │   │   │   ├── config_editor.py
│   │   │   │   ├── format_editor.py
│   │   │   │   ├── format_preview_widget.py
│   │   │   │   ├── main_widget.py
│   │   │   │   ├── output_preview_table.py
│   │   │   │   └── preview_widget.py
│   │   │   ├── utils/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ai_background_remover.py
│   │   │   │   ├── config_manager.py
│   │   │   │   ├── exceptions.py
│   │   │   │   ├── font_manager.py
│   │   │   │   ├── image_utils.py
│   │   │   │   └── path_resolver.py
│   │   │   ├── __init__.py
│   │   │   └── plugin.py
│   │   ├── DOCUMENTATION.md
│   │   ├── README.md
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
│   ├── settings_manager.py
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