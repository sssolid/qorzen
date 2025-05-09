from __future__ import annotations
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path
def pre_install(context: Dict[str, Any]) -> None:
    print('Example Plugin: Pre-install hook called')
    print(f'Installation context: {json.dumps(context, indent=2)}')
    package_path = context.get('package_path', '')
    force = context.get('force', False)
    skip_verification = context.get('skip_verification', False)
    print(f'Installing from: {package_path}')
    print(f'Force install: {force}')
    print(f'Skip verification: {skip_verification}')
def post_install(context: Dict[str, Any]) -> None:
    print('Example Plugin: Post-install hook called')
    install_path = context.get('install_path', '')
    if install_path:
        data_dir = Path(install_path) / 'data'
        os.makedirs(data_dir, exist_ok=True)
        example_file = data_dir / 'example_data.json'
        with open(example_file, 'w') as f:
            json.dump({'created_by': 'post_install hook', 'version': '1.0.0', 'data': {'example': 'This is example data created during installation'}}, f, indent=2)
        print(f'Created example data file: {example_file}')
    print('Example Plugin installation completed successfully')
def pre_uninstall(context: Dict[str, Any]) -> None:
    print('Example Plugin: Pre-uninstall hook called')
    keep_data = context.get('keep_data', False)
    print(f'Keep data: {keep_data}')
    if not keep_data:
        print('WARNING: All plugin data will be removed!')
        install_path = context.get('install_path', '')
        if install_path:
            data_dir = Path(install_path) / 'data'
            if data_dir.exists():
                print(f'Would back up data from: {data_dir}')
def post_uninstall(context: Dict[str, Any]) -> None:
    print('Example Plugin: Post-uninstall hook called')
    success = context.get('success', False)
    print(f'Uninstallation successful: {success}')
    print('Example Plugin uninstallation completed')
def pre_update(context: Dict[str, Any]) -> None:
    print('Example Plugin: Pre-update hook called')
    current_version = context.get('current_version', 'unknown')
    new_version = context.get('new_version', 'unknown')
    print(f'Updating from version {current_version} to {new_version}')
    if current_version == '0.9.0' and new_version == '1.0.0':
        print('Performing special update steps for 0.9.0 -> 1.0.0 update')
def post_update(context: Dict[str, Any]) -> None:
    print('Example Plugin: Post-update hook called')
    success = context.get('success', False)
    if not success:
        print('Update did not complete successfully')
        return
    current_version = context.get('current_version', 'unknown')
    new_version = context.get('new_version', 'unknown')
    install_path = context.get('install_path', '')
    if install_path:
        data_dir = Path(install_path) / 'data'
        os.makedirs(data_dir, exist_ok=True)
        example_file = data_dir / 'example_data.json'
        if example_file.exists():
            try:
                with open(example_file, 'r') as f:
                    data = json.load(f)
                data['updated_by'] = 'post_update hook'
                data['version'] = new_version
                data['update_info'] = {'previous_version': current_version, 'update_date': context.get('update_date', 'unknown')}
                with open(example_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f'Updated example data file: {example_file}')
            except Exception as e:
                print(f'Error updating example data file: {e}')
        else:
            with open(example_file, 'w') as f:
                json.dump({'created_by': 'post_update hook', 'version': new_version, 'data': {'example': 'This is example data created during update'}}, f, indent=2)
            print(f'Created example data file: {example_file}')
    print(f'Example Plugin updated successfully to version {new_version}')