from __future__ import annotations
'\nApplication presets for common external applications.\n\nThis module provides presets for commonly used applications to simplify\nthe process of adding them to the Application Launcher.\n'
import os
import platform
import shutil
from typing import Dict, List, Optional, Any
from .plugin import ApplicationConfig, ArgumentConfig, ArgumentType
def get_common_applications() -> List[ApplicationConfig]:
    system = platform.system()
    apps = []
    if system == 'Windows':
        apps.extend(_get_windows_applications())
    elif system == 'Darwin':
        apps.extend(_get_macos_applications())
    elif system == 'Linux':
        apps.extend(_get_linux_applications())
    apps.extend(_get_cross_platform_applications())
    return apps
def _get_windows_applications() -> List[ApplicationConfig]:
    apps = []
    notepad_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'notepad.exe')
    if os.path.exists(notepad_path):
        apps.append(ApplicationConfig(id='windows_notepad', name='Notepad', executable_path=notepad_path, description='Windows Notepad text editor', category='Text Editors', arguments=[ArgumentConfig(name='file', arg_type=ArgumentType.FILE_INPUT, description='File to open', required=False, file_filter='Text Files (*.txt);;All Files (*.*)')]))
    cmd_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'system32\\cmd.exe')
    if os.path.exists(cmd_path):
        apps.append(ApplicationConfig(id='windows_cmd', name='Command Prompt', executable_path=cmd_path, description='Windows Command Prompt', category='Terminals', arguments=[ArgumentConfig(name='command', arg_type=ArgumentType.TEXT_INPUT, description='Command to execute', required=False, prefix='/C ')]))
    powershell_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32\\WindowsPowerShell\\v1.0\\powershell.exe')
    if os.path.exists(powershell_path):
        apps.append(ApplicationConfig(id='windows_powershell', name='PowerShell', executable_path=powershell_path, description='Windows PowerShell', category='Terminals', arguments=[ArgumentConfig(name='command', arg_type=ArgumentType.TEXT_INPUT, description='Command to execute', required=False, prefix='-Command ')], output_patterns=['*.txt', '*.csv', '*.json', '*.xml', '*.log']))
    mspaint_path = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'system32\\mspaint.exe')
    if os.path.exists(mspaint_path):
        apps.append(ApplicationConfig(id='windows_paint', name='Paint', executable_path=mspaint_path, description='Windows Paint graphics editor', category='Graphics', arguments=[ArgumentConfig(name='file', arg_type=ArgumentType.FILE_INPUT, description='Image to open', required=False, file_filter='Images (*.bmp *.jpg *.jpeg *.png *.gif);;All Files (*.*)')]))
    return apps
def _get_macos_applications() -> List[ApplicationConfig]:
    apps = []
    terminal_path = '/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal'
    if os.path.exists(terminal_path):
        apps.append(ApplicationConfig(id='macos_terminal', name='Terminal', executable_path=terminal_path, description='macOS Terminal', category='Terminals', arguments=[ArgumentConfig(name='command', arg_type=ArgumentType.TEXT_INPUT, description='Command to execute', required=False, prefix='-e ')]))
    textedit_path = '/Applications/TextEdit.app/Contents/MacOS/TextEdit'
    if os.path.exists(textedit_path):
        apps.append(ApplicationConfig(id='macos_textedit', name='TextEdit', executable_path=textedit_path, description='macOS TextEdit text editor', category='Text Editors', arguments=[ArgumentConfig(name='file', arg_type=ArgumentType.FILE_INPUT, description='File to open', required=False, file_filter='Text Files (*.txt *.rtf);;All Files (*.*)')]))
    return apps
def _get_linux_applications() -> List[ApplicationConfig]:
    apps = []
    terminals = [('/usr/bin/gnome-terminal', 'GNOME Terminal'), ('/usr/bin/konsole', 'KDE Konsole'), ('/usr/bin/xterm', 'XTerm'), ('/usr/bin/terminator', 'Terminator'), ('/usr/bin/xfce4-terminal', 'XFCE Terminal')]
    for terminal_path, terminal_name in terminals:
        if os.path.exists(terminal_path):
            apps.append(ApplicationConfig(id=f"linux_{terminal_name.lower().replace(' ', '_')}", name=terminal_name, executable_path=terminal_path, description=f'{terminal_name} terminal emulator', category='Terminals', arguments=[ArgumentConfig(name='command', arg_type=ArgumentType.TEXT_INPUT, description='Command to execute', required=False, prefix='--execute ')]))
            break
    editors = [('/usr/bin/gedit', 'Gedit'), ('/usr/bin/kwrite', 'KWrite'), ('/usr/bin/leafpad', 'Leafpad'), ('/usr/bin/mousepad', 'Mousepad')]
    for editor_path, editor_name in editors:
        if os.path.exists(editor_path):
            apps.append(ApplicationConfig(id=f'linux_{editor_name.lower()}', name=editor_name, executable_path=editor_path, description=f'{editor_name} text editor', category='Text Editors', arguments=[ArgumentConfig(name='file', arg_type=ArgumentType.FILE_INPUT, description='File to open', required=False, file_filter='Text Files (*.txt);;All Files (*.*)')]))
            break
    return apps
def _get_cross_platform_applications() -> List[ApplicationConfig]:
    apps = []
    python_path = shutil.which('python') or shutil.which('python3')
    if python_path:
        apps.append(ApplicationConfig(id='python_interpreter', name='Python', executable_path=python_path, description='Python interpreter', category='Development', arguments=[ArgumentConfig(name='script', arg_type=ArgumentType.FILE_INPUT, description='Python script to run', required=True, file_filter='Python Files (*.py);;All Files (*.*)'), ArgumentConfig(name='args', arg_type=ArgumentType.TEXT_INPUT, description='Command line arguments', required=False)], environment_variables={'PYTHONUNBUFFERED': '1'}, output_patterns=['*.txt', '*.csv', '*.json', '*.xml', '*.log', '*.png', '*.jpg']))
    node_path = shutil.which('node')
    if node_path:
        apps.append(ApplicationConfig(id='nodejs', name='Node.js', executable_path=node_path, description='Node.js JavaScript runtime', category='Development', arguments=[ArgumentConfig(name='script', arg_type=ArgumentType.FILE_INPUT, description='JavaScript file to run', required=True, file_filter='JavaScript Files (*.js);;All Files (*.*)'), ArgumentConfig(name='args', arg_type=ArgumentType.TEXT_INPUT, description='Command line arguments', required=False)], output_patterns=['*.txt', '*.csv', '*.json', '*.xml', '*.log', '*.html']))
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        apps.append(ApplicationConfig(id='ffmpeg', name='FFmpeg', executable_path=ffmpeg_path, description='FFmpeg media converter', category='Media', arguments=[ArgumentConfig(name='input', arg_type=ArgumentType.FILE_INPUT, description='Input video file', required=True, prefix='-i ', file_filter='Video Files (*.mp4 *.avi *.mkv *.mov);;Audio Files (*.mp3 *.wav *.ogg);;All Files (*.*)'), ArgumentConfig(name='options', arg_type=ArgumentType.TEXT_INPUT, description='Conversion options', required=False, value='-c:v libx264 -preset medium -crf 23'), ArgumentConfig(name='output', arg_type=ArgumentType.FILE_OUTPUT, description='Output file', required=True, file_filter='Video Files (*.mp4 *.avi *.mkv *.mov);;Audio Files (*.mp3 *.wav *.ogg);;All Files (*.*)')], output_patterns=['*.mp4', '*.avi', '*.mkv', '*.mov', '*.mp3', '*.wav', '*.ogg']))
    convert_path = shutil.which('convert')
    if convert_path:
        apps.append(ApplicationConfig(id='imagemagick', name='ImageMagick', executable_path=convert_path, description='ImageMagick image converter', category='Graphics', arguments=[ArgumentConfig(name='input', arg_type=ArgumentType.FILE_INPUT, description='Input image file', required=True, file_filter='Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff);;All Files (*.*)'), ArgumentConfig(name='options', arg_type=ArgumentType.TEXT_INPUT, description='Conversion options', required=False, value='-resize 800x600'), ArgumentConfig(name='output', arg_type=ArgumentType.FILE_OUTPUT, description='Output file', required=True, file_filter='Image Files (*.png *.jpg *.jpeg *.gif *.bmp *.tiff);;All Files (*.*)')], output_patterns=['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp', '*.tiff']))
    return apps
def create_custom_script_app(script_type: str, script_content: str, name: str, description: str='', category: str='Scripts') -> ApplicationConfig:
    import tempfile
    import os
    import platform
    extension_map = {'bash': '.sh', 'batch': '.bat' if platform.system() == 'Windows' else '.sh', 'python': '.py', 'powershell': '.ps1', 'javascript': '.js'}
    extension = extension_map.get(script_type.lower(), '.txt')
    with tempfile.NamedTemporaryFile(suffix=extension, delete=False, mode='w') as f:
        f.write(script_content)
        temp_path = f.name
    if platform.system() != 'Windows' and script_type.lower() in ('bash', 'batch'):
        os.chmod(temp_path, 493)
    executable_map = {'bash': shutil.which('bash') or '/bin/bash', 'batch': 'cmd.exe' if platform.system() == 'Windows' else shutil.which('bash') or '/bin/bash', 'python': shutil.which('python') or shutil.which('python3') or 'python', 'powershell': shutil.which('powershell') or 'powershell', 'javascript': shutil.which('node') or 'node'}
    executable = executable_map.get(script_type.lower(), '')
    arguments = []
    if script_type.lower() in ('bash', 'batch', 'powershell'):
        arguments.append(ArgumentConfig(name='script', arg_type=ArgumentType.STATIC, value=temp_path, description='Script file path', required=True))
    arguments.append(ArgumentConfig(name='args', arg_type=ArgumentType.TEXT_INPUT, description='Command line arguments', required=False))
    return ApplicationConfig(id=f'custom_script_{os.urandom(4).hex()}', name=name, executable_path=executable, description=description, category=category, arguments=arguments, output_patterns=['*.txt', '*.csv', '*.json', '*.xml', '*.log'], show_console_output=True)