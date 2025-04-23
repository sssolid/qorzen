#!/usr/bin/env python3
"""
Frontend Structure Mapper - Generate comprehensive code structure representations for Vue 3 + TypeScript projects.

This tool analyzes Vue and TypeScript files in frontend projects and generates detailed structural
representations that include components, props, emits, methods, computed properties, and TypeScript types.
"""
from __future__ import annotations

import os
import json
import re
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("frontend_structure_mapper")


class OutputFormat(Enum):
    """Supported output formats for the code structure representation."""

    JSON = auto()
    MARKDOWN = auto()
    MERMAID = auto()
    TEXT = auto()


class FileType(Enum):
    """Types of frontend files."""

    VUE = auto()
    TYPESCRIPT = auto()
    JAVASCRIPT = auto()
    HTML = auto()
    CSS = auto()
    SCSS = auto()
    JSON = auto()
    UNKNOWN = auto()


@dataclass
class PropInfo:
    """Information about a Vue component prop."""

    name: str
    type: Optional[str] = None
    required: bool = False
    default_value: Optional[str] = None
    validator: Optional[str] = None
    description: Optional[str] = None


@dataclass
class EmitInfo:
    """Information about a Vue component emit."""

    name: str
    payload_type: Optional[str] = None
    description: Optional[str] = None


@dataclass
class MethodInfo:
    """Information about a method in a component or class."""

    name: str
    args: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    description: Optional[str] = None
    is_async: bool = False
    source_code: Optional[str] = None
    arg_types: Dict[str, str] = field(default_factory=dict)


@dataclass
class ComputedInfo:
    """Information about a computed property."""

    name: str
    return_type: Optional[str] = None
    description: Optional[str] = None
    getter: Optional[str] = None
    setter: Optional[bool] = None


@dataclass
class WatchInfo:
    """Information about a watch property."""

    target: str
    handler: str
    immediate: bool = False
    deep: bool = False


@dataclass
class HookInfo:
    """Information about a lifecycle hook."""

    name: str
    source_code: Optional[str] = None


@dataclass
class TypeInfo:
    """Information about a TypeScript type or interface."""

    name: str
    kind: str  # "interface", "type", "enum", etc.
    properties: Dict[str, str] = field(default_factory=dict)
    extends: List[str] = field(default_factory=list)
    description: Optional[str] = None
    source_code: Optional[str] = None


@dataclass
class VueComponentInfo:
    """Information about a Vue component."""

    name: str
    file_path: Path
    component_type: str = "Options API"  # "Options API" or "Composition API"
    template: Optional[str] = None
    props: Dict[str, PropInfo] = field(default_factory=dict)
    emits: Dict[str, EmitInfo] = field(default_factory=dict)
    data: Dict[str, str] = field(default_factory=dict)
    computed: Dict[str, ComputedInfo] = field(default_factory=dict)
    methods: Dict[str, MethodInfo] = field(default_factory=dict)
    watchers: Dict[str, WatchInfo] = field(default_factory=dict)
    hooks: Dict[str, HookInfo] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    refs: Dict[str, str] = field(default_factory=dict)
    reactive_state: Dict[str, str] = field(default_factory=dict)
    provide: List[str] = field(default_factory=list)
    inject: List[str] = field(default_factory=list)
    components: Dict[str, str] = field(default_factory=dict)
    setup_return: List[str] = field(default_factory=list)
    directives: List[str] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class TypeScriptFileInfo:
    """Information about a TypeScript file."""

    name: str
    file_path: Path
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    types: Dict[str, TypeInfo] = field(default_factory=dict)
    functions: Dict[str, MethodInfo] = field(default_factory=dict)
    classes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    constants: Dict[str, str] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None


@dataclass
class StyleInfo:
    """Information about styles in Vue components."""

    language: str = "css"  # css, scss, less, etc.
    scoped: bool = False
    module: bool = False
    content: Optional[str] = None


@dataclass
class DirectoryInfo:
    """Information about a directory in the project."""

    name: str
    path: Path
    vue_components: Dict[str, VueComponentInfo] = field(default_factory=dict)
    typescript_files: Dict[str, TypeScriptFileInfo] = field(default_factory=dict)
    subdirectories: Dict[str, "DirectoryInfo"] = field(default_factory=dict)
    other_files: List[str] = field(default_factory=list)


@dataclass
class FrontendProjectInfo:
    """Information about the entire frontend project."""

    name: str
    root_path: Path
    project_type: str = "Vue 3"  # Vue 3, React, etc.
    structure: DirectoryInfo = field(
        default_factory=lambda: DirectoryInfo(name="", path=Path("."))
    )
    package_json: Optional[Dict[str, Any]] = None
    tsconfig_json: Optional[Dict[str, Any]] = None


class VueParser:
    """Parser for Vue single-file components."""

    def __init__(self, include_template: bool = False) -> None:
        """
        Initialize the Vue parser.

        Args:
            include_template: Whether to include the template content in the output
        """
        self.include_template = include_template

    def parse(self, file_path: Path) -> VueComponentInfo:
        """
        Parse a Vue single-file component.

        Args:
            file_path: Path to the Vue file

        Returns:
            VueComponentInfo object containing component data
        """
        component_name = file_path.stem
        component_info = VueComponentInfo(name=component_name, file_path=file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract template
            template_match = re.search(r"<template>([\s\S]*?)</template>", content)
            if template_match and self.include_template:
                component_info.template = template_match.group(1).strip()

            # Extract script
            script_match = re.search(r"<script[^>]*>([\s\S]*?)</script>", content)
            if script_match:
                script_content = script_match.group(1).strip()
                script_lang = (
                    "ts"
                    if '<script lang="ts"' in content
                    or '<script setup lang="ts"' in content
                    else "js"
                )
                is_setup = "<script setup" in content

                if is_setup:
                    component_info.component_type = "Composition API (script setup)"
                    self._parse_script_setup(
                        script_content, component_info, script_lang
                    )
                else:
                    # Check if it's using defineComponent with Composition API
                    if "defineComponent" in script_content and (
                        "setup(" in script_content or "setup:" in script_content
                    ):
                        component_info.component_type = "Composition API"
                        self._parse_composition_api(
                            script_content, component_info, script_lang
                        )
                    else:
                        component_info.component_type = "Options API"
                        self._parse_options_api(
                            script_content, component_info, script_lang
                        )

            # Extract style
            style_match = re.search(r"<style[^>]*>([\s\S]*?)</style>", content)
            if style_match:
                style_attrs = re.search(r"<style([^>]*)>", content)
                style_info = StyleInfo()

                if style_attrs:
                    attrs = style_attrs.group(1)
                    if "scoped" in attrs:
                        style_info.scoped = True
                    if "module" in attrs:
                        style_info.module = True
                    lang_match = re.search(r'lang="([^"]+)"', attrs)
                    if lang_match:
                        style_info.language = lang_match.group(1)

                # We don't store style content in the component info by default

            return component_info

        except Exception as e:
            logger.error(f"Error parsing Vue component {file_path}: {str(e)}")
            return component_info

    def _parse_script_setup(
        self, script_content: str, component_info: VueComponentInfo, lang: str
    ) -> None:
        """
        Parse <script setup> content.

        Args:
            script_content: The script content
            component_info: VueComponentInfo to update
            lang: Script language (ts or js)
        """
        # Extract imports
        component_info.imports = self._extract_imports(script_content)

        # Extract defineProps
        props_match = re.search(
            r"const\s+props\s*=\s*defineProps<([^>]+)>\(\)", script_content
        )
        if props_match:
            # TypeScript interface style props
            props_interface = props_match.group(1).strip()
            self._parse_props_interface(props_interface, component_info)
        else:
            props_match = re.search(
                r"const\s+props\s*=\s*defineProps\(([^)]+)\)", script_content
            )
            if props_match:
                # Object style props
                props_obj = props_match.group(1).strip()
                self._parse_props_object(props_obj, component_info)

        # Extract defineEmits
        emits_match = re.search(
            r"const\s+emit\s*=\s*defineEmits<([^>]+)>\(\)", script_content
        )
        if emits_match:
            # TypeScript interface style emits
            emits_interface = emits_match.group(1).strip()
            self._parse_emits_interface(emits_interface, component_info)
        else:
            emits_match = re.search(
                r"const\s+emit\s*=\s*defineEmits\(\s*(\[[^\]]+\])\s*\)", script_content
            )
            if emits_match:
                # Array style emits
                emits_array = emits_match.group(1).strip()
                self._parse_emits_array(emits_array, component_info)

        # Extract refs
        ref_matches = re.findall(r"const\s+(\w+)\s*=\s*ref\(([^)]*)\)", script_content)
        for match in ref_matches:
            name, value = match
            component_info.refs[name] = value.strip() or "undefined"

        # Extract reactive state
        reactive_matches = re.findall(
            r"const\s+(\w+)\s*=\s*reactive\(([^)]+)\)", script_content
        )
        for match in reactive_matches:
            name, value = match
            component_info.reactive_state[name] = value.strip()

        # Extract computed properties
        computed_matches = re.findall(
            r"const\s+(\w+)\s*=\s*computed\(\s*\(\)\s*=>\s*([^}]+)\)", script_content
        )
        for match in computed_matches:
            name, expression = match
            computed_info = ComputedInfo(name=name, getter=expression.strip())
            component_info.computed[name] = computed_info

        # Extract functions/methods
        function_matches = re.findall(
            r"(async\s+)?function\s+(\w+)\s*\(([^)]*)\)[^{]*{", script_content
        )
        for match in function_matches:
            is_async, name, args = match
            method_info = MethodInfo(
                name=name, args=self._parse_argument_list(args), is_async=bool(is_async)
            )
            component_info.methods[name] = method_info

        # Also catch arrow functions
        arrow_matches = re.findall(
            r"const\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>", script_content
        )
        for match in arrow_matches:
            name, is_async = match
            if name not in component_info.computed and name not in component_info.refs:
                method_info = MethodInfo(name=name, is_async=bool(is_async))
                component_info.methods[name] = method_info

        # Extract watchers
        watch_matches = re.findall(
            r"watch\(\s*(?:\/\*[^*]*\*\/\s*)?([^,]+),\s*(?:\/\*[^*]*\*\/\s*)?\((?:[^)]+)\)\s*=>\s*{",
            script_content,
        )
        for match in watch_matches:
            target = match.strip()
            watcher_info = WatchInfo(
                target=target, handler=f"[Inline watcher for {target}]"
            )
            component_info.watchers[target] = watcher_info

        # Extract provide/inject
        provide_matches = re.findall(
            r'provide\(\s*[\'"]?(\w+)[\'"]?\s*,', script_content
        )
        for match in provide_matches:
            component_info.provide.append(match)

        inject_matches = re.findall(
            r'const\s+(\w+)\s*=\s*inject\(\s*[\'"]?(\w+)[\'"]?', script_content
        )
        for match in inject_matches:
            var_name, key = match
            component_info.inject.append(f"{key} as {var_name}")

        # Extract lifecycle hooks
        hook_patterns = [
            r"onMounted\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onBeforeMount\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onBeforeUpdate\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onUpdated\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onBeforeUnmount\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onUnmounted\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onActivated\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onDeactivated\(\s*\(\)\s*=>\s*{([^}]+)}",
            r"onErrorCaptured\(\s*\(\)\s*=>\s*{([^}]+)}",
        ]

        for pattern in hook_patterns:
            hook_name = pattern.split("\\")[0].replace("on", "").lower()
            match = re.search(pattern, script_content)
            if match:
                hook_info = HookInfo(name=hook_name, source_code=match.group(1).strip())
                component_info.hooks[hook_name] = hook_info

    def _parse_composition_api(
        self, script_content: str, component_info: VueComponentInfo, lang: str
    ) -> None:
        """
        Parse Composition API script content.

        Args:
            script_content: The script content
            component_info: VueComponentInfo to update
            lang: Script language (ts or js)
        """
        # Extract imports
        component_info.imports = self._extract_imports(script_content)

        # Extract setup function content
        setup_match = re.search(
            r"setup\s*\(([^)]*)\)\s*{([\s\S]*?)return\s+({[\s\S]*?});?\s*}",
            script_content,
        )
        if setup_match:
            setup_args, setup_body, setup_return = setup_match.groups()

            # Process setup arguments (props, context)
            if setup_args:
                args = [arg.strip() for arg in setup_args.split(",")]
                for arg in args:
                    if arg.startswith("props"):
                        # Props are usually destructured or used directly
                        pass
                    elif "emit" in arg or "context" in arg:
                        # Context might contain emit, attrs, slots
                        pass

            # Process refs, reactive state in setup body
            ref_matches = re.findall(r"const\s+(\w+)\s*=\s*ref\(([^)]*)\)", setup_body)
            for match in ref_matches:
                name, value = match
                component_info.refs[name] = value.strip() or "undefined"

            reactive_matches = re.findall(
                r"const\s+(\w+)\s*=\s*reactive\(([^)]+)\)", setup_body
            )
            for match in reactive_matches:
                name, value = match
                component_info.reactive_state[name] = value.strip()

            # Process computed properties
            computed_matches = re.findall(
                r"const\s+(\w+)\s*=\s*computed\(\s*\(\)\s*=>\s*([^}]+)\)", setup_body
            )
            for match in computed_matches:
                name, expression = match
                computed_info = ComputedInfo(name=name, getter=expression.strip())
                component_info.computed[name] = computed_info

            # Process methods
            function_matches = re.findall(
                r"const\s+(\w+)\s*=\s*(async\s+)?\([^)]*\)\s*=>\s*{", setup_body
            )
            for match in function_matches:
                name, is_async = match
                if (
                    name not in component_info.computed
                    and name not in component_info.refs
                ):
                    method_info = MethodInfo(name=name, is_async=bool(is_async))
                    component_info.methods[name] = method_info

            # Process return value to find exposed variables
            if setup_return:
                # Remove curly braces and split by commas
                return_vars = setup_return.strip()[1:-1].split(",")
                for var in return_vars:
                    var = var.strip()
                    if var and ":" not in var:  # Skip object property initialization
                        component_info.setup_return.append(var)

        # Look for props definition
        props_match = re.search(r"props:\s*({[\s\S]*?})", script_content)
        if props_match:
            props_obj = props_match.group(1).strip()
            self._parse_props_object(props_obj, component_info)

        # Look for emits definition
        emits_match = re.search(r"emits:\s*(\[[^\]]*\])", script_content)
        if emits_match:
            emits_array = emits_match.group(1).strip()
            self._parse_emits_array(emits_array, component_info)
        else:
            emits_match = re.search(r"emits:\s*({[\s\S]*?})", script_content)
            if emits_match:
                emits_obj = emits_match.group(1).strip()
                self._parse_emits_object(emits_obj, component_info)

    def _parse_options_api(
        self, script_content: str, component_info: VueComponentInfo, lang: str
    ) -> None:
        """
        Parse Options API script content.

        Args:
            script_content: The script content
            component_info: VueComponentInfo to update
            lang: Script language (ts or js)
        """
        # Extract imports
        component_info.imports = self._extract_imports(script_content)

        # Extract component name if defined
        name_match = re.search(r'name:\s*[\'"]([^\'"]+)[\'"]', script_content)
        if name_match:
            component_info.name = name_match.group(1)

        # Extract props
        props_match = re.search(r"props:\s*({[\s\S]*?})", script_content)
        if props_match:
            props_obj = props_match.group(1).strip()
            self._parse_props_object(props_obj, component_info)
        else:
            props_match = re.search(r"props:\s*(\[[^\]]*\])", script_content)
            if props_match:
                props_array = props_match.group(1).strip()
                self._parse_props_array(props_array, component_info)

        # Extract emits
        emits_match = re.search(r"emits:\s*(\[[^\]]*\])", script_content)
        if emits_match:
            emits_array = emits_match.group(1).strip()
            self._parse_emits_array(emits_array, component_info)
        else:
            emits_match = re.search(r"emits:\s*({[\s\S]*?})", script_content)
            if emits_match:
                emits_obj = emits_match.group(1).strip()
                self._parse_emits_object(emits_obj, component_info)

        # Extract data
        data_match = re.search(
            r"data\s*\(\s*\)\s*{\s*return\s*({[\s\S]*?})\s*;?\s*}", script_content
        )
        if data_match:
            data_obj = data_match.group(1).strip()
            self._parse_data_object(data_obj, component_info)

        # Extract computed properties
        computed_match = re.search(
            r"computed:\s*({[\s\S]*?})(?:,\s*\w+:|,\s*}|$)", script_content
        )
        if computed_match:
            computed_obj = computed_match.group(1).strip()
            self._parse_computed_object(computed_obj, component_info)

        # Extract methods
        methods_match = re.search(
            r"methods:\s*({[\s\S]*?})(?:,\s*\w+:|,\s*}|$)", script_content
        )
        if methods_match:
            methods_obj = methods_match.group(1).strip()
            self._parse_methods_object(methods_obj, component_info)

        # Extract watchers
        watch_match = re.search(
            r"watch:\s*({[\s\S]*?})(?:,\s*\w+:|,\s*}|$)", script_content
        )
        if watch_match:
            watch_obj = watch_match.group(1).strip()
            self._parse_watch_object(watch_obj, component_info)

        # Extract components
        components_match = re.search(
            r"components:\s*({[\s\S]*?})(?:,\s*\w+:|,\s*}|$)", script_content
        )
        if components_match:
            components_obj = components_match.group(1).strip()
            self._parse_components_object(components_obj, component_info)

        # Extract lifecycle hooks
        hooks = [
            "beforeCreate",
            "created",
            "beforeMount",
            "mounted",
            "beforeUpdate",
            "updated",
            "beforeDestroy",
            "destroyed",
            "activated",
            "deactivated",
            "errorCaptured",
        ]

        for hook in hooks:
            hook_match = re.search(
                rf"{hook}\s*\(\s*\)\s*{{([\s\S]*?)}}", script_content
            )
            if hook_match:
                hook_content = hook_match.group(1).strip()
                hook_info = HookInfo(name=hook, source_code=hook_content)
                component_info.hooks[hook] = hook_info

        # Extract provide/inject
        provide_match = re.search(
            r"provide:\s*({[\s\S]*?})(?:,\s*\w+:|,\s*}|$)", script_content
        )
        if provide_match:
            provide_obj = provide_match.group(1).strip()
            # Simple extraction - just get the keys
            key_matches = re.findall(r'[\'"]?(\w+)[\'"]?\s*:', provide_obj)
            component_info.provide = key_matches

        inject_match = re.search(r"inject:\s*(\[[^\]]*\])", script_content)
        if inject_match:
            inject_array = inject_match.group(1).strip()
            # Remove array brackets and strip whitespace
            content = inject_array[1:-1]
            items = [
                item.strip().strip("'\"") for item in content.split(",") if item.strip()
            ]
            component_info.inject = items
        else:
            inject_match = re.search(
                r"inject:\s*({[\s\S]*?})(?:,\s*\w+:|,\s*}|$)", script_content
            )
            if inject_match:
                inject_obj = inject_match.group(1).strip()
                # Get keys from object
                key_matches = re.findall(r'[\'"]?(\w+)[\'"]?\s*:', inject_obj)
                component_info.inject = key_matches

        # Extract mixins
        mixins_match = re.search(r"mixins:\s*(\[[^\]]*\])", script_content)
        if mixins_match:
            mixins_array = mixins_match.group(1).strip()
            mixin_matches = re.findall(r"(\w+)", mixins_array)
            component_info.mixins = mixin_matches

        # Extract directives
        directives_match = re.search(
            r"directives:\s*({[\s\S]*?})(?:,\s*\w+:|,\s*}|$)", script_content
        )
        if directives_match:
            directives_obj = directives_match.group(1).strip()
            directive_matches = re.findall(r'[\'"]?(\w+)[\'"]?\s*:', directives_obj)
            component_info.directives = directive_matches

    def _parse_props_interface(
        self, props_interface: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse TypeScript interface style props.

        Args:
            props_interface: The props interface content
            component_info: VueComponentInfo to update
        """
        # This is a simplified parsing of TypeScript interfaces
        # A proper parser would use TypeScript's compiler API
        prop_entries = re.findall(r"(\w+)\??\s*:\s*([^;]+)", props_interface)
        for prop_name, prop_type in prop_entries:
            is_required = "?" not in prop_name
            prop_name = prop_name.rstrip("?")

            prop_info = PropInfo(
                name=prop_name, type=prop_type.strip(), required=is_required
            )
            component_info.props[prop_name] = prop_info

    def _parse_props_object(
        self, props_obj: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse object style props.

        Args:
            props_obj: The props object content
            component_info: VueComponentInfo to update
        """
        # Extract individual prop definitions using regex
        # This is a simplified approach and might not handle all edge cases
        prop_entries = re.findall(
            r'[\'"]?(\w+)[\'"]?\s*:\s*({[\s\S]*?})(?:,\s*[\'"]?\w+[\'"]?:|,\s*}|$)',
            props_obj,
        )

        for prop_name, prop_def in prop_entries:
            prop_info = PropInfo(name=prop_name)

            # Extract type
            type_match = re.search(r"type:\s*(\w+|\[[\s\S]*?\])", prop_def)
            if type_match:
                prop_info.type = type_match.group(1).strip()

            # Extract required flag
            required_match = re.search(r"required:\s*(true|false)", prop_def)
            if required_match:
                prop_info.required = required_match.group(1) == "true"

            # Extract default value
            default_match = re.search(r"default:\s*([^,}]+)", prop_def)
            if default_match:
                prop_info.default_value = default_match.group(1).strip()

            component_info.props[prop_name] = prop_info

        # Also look for simple prop names without detailed config
        simple_props = re.findall(r'[\'"]?(\w+)[\'"]?(?:,|$)', props_obj)
        for prop_name in simple_props:
            if prop_name not in component_info.props:
                component_info.props[prop_name] = PropInfo(name=prop_name)

    def _parse_props_array(
        self, props_array: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse array style props.

        Args:
            props_array: The props array content
            component_info: VueComponentInfo to update
        """
        # Remove array brackets and split by commas
        content = props_array[1:-1]
        prop_names = [
            name.strip().strip("'\"") for name in content.split(",") if name.strip()
        ]

        for prop_name in prop_names:
            component_info.props[prop_name] = PropInfo(name=prop_name)

    def _parse_emits_interface(
        self, emits_interface: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse TypeScript interface style emits.

        Args:
            emits_interface: The emits interface content
            component_info: VueComponentInfo to update
        """
        # Extract emit names and their payload types
        emit_entries = re.findall(r"(\w+)(?:\s*\(([^)]*)\))?\s*:", emits_interface)
        for emit_name, payload in emit_entries:
            emit_info = EmitInfo(
                name=emit_name, payload_type=payload.strip() if payload else None
            )
            component_info.emits[emit_name] = emit_info

    def _parse_emits_array(
        self, emits_array: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse array style emits.

        Args:
            emits_array: The emits array content
            component_info: VueComponentInfo to update
        """
        # Remove array brackets and split by commas
        content = emits_array[1:-1]
        emit_names = [
            name.strip().strip("'\"") for name in content.split(",") if name.strip()
        ]

        for emit_name in emit_names:
            component_info.emits[emit_name] = EmitInfo(name=emit_name)

    def _parse_emits_object(
        self, emits_obj: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse object style emits.

        Args:
            emits_obj: The emits object content
            component_info: VueComponentInfo to update
        """
        # Extract emit names
        emit_entries = re.findall(r'[\'"]?(\w+)[\'"]?\s*:', emits_obj)
        for emit_name in emit_entries:
            component_info.emits[emit_name] = EmitInfo(name=emit_name)

    def _parse_data_object(
        self, data_obj: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse data object.

        Args:
            data_obj: The data object content
            component_info: VueComponentInfo to update
        """
        # Extract data properties using regex
        data_entries = re.findall(r'[\'"]?(\w+)[\'"]?\s*:\s*([^,}]+)', data_obj)
        for prop_name, prop_value in data_entries:
            component_info.data[prop_name] = prop_value.strip()

    def _parse_computed_object(
        self, computed_obj: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse computed properties object.

        Args:
            computed_obj: The computed object content
            component_info: VueComponentInfo to update
        """
        # Extract simple computed properties (just getters)
        computed_getters = re.findall(
            r'[\'"]?(\w+)[\'"]?\s*\(\s*\)\s*{([\s\S]*?)return([^;]+);', computed_obj
        )
        for name, _, getter in computed_getters:
            computed_info = ComputedInfo(name=name, getter=getter.strip())
            component_info.computed[name] = computed_info

        # Extract computed properties with get/set
        computed_get_set = re.findall(
            r'[\'"]?(\w+)[\'"]?\s*:\s*{[\s\S]*?get\s*\(\s*\)\s*{[\s\S]*?return([^;]+);[\s\S]*?}(?:[\s\S]*?set\s*\([^)]*\)\s*{)?',
            computed_obj,
        )
        for name, getter in computed_get_set:
            setter_exists = (
                f"set("
                in computed_obj[computed_obj.find(name) : computed_obj.find(name) + 200]
            )
            computed_info = ComputedInfo(
                name=name, getter=getter.strip(), setter=setter_exists
            )
            component_info.computed[name] = computed_info

    def _parse_methods_object(
        self, methods_obj: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse methods object.

        Args:
            methods_obj: The methods object content
            component_info: VueComponentInfo to update
        """
        # Extract method definitions
        method_defs = re.findall(
            r'[\'"]?(\w+)[\'"]?\s*(?::\s*)?(async\s+)?function\s*\(([^)]*)\)',
            methods_obj,
        )
        for name, is_async, args in method_defs:
            method_info = MethodInfo(
                name=name, args=self._parse_argument_list(args), is_async=bool(is_async)
            )
            component_info.methods[name] = method_info

        # Extract method definitions (ES6 shorthand)
        es6_method_defs = re.findall(r'[\'"]?(\w+)[\'"]?\s*\(([^)]*)\)', methods_obj)
        for name, args in es6_method_defs:
            if name not in component_info.methods:
                method_info = MethodInfo(
                    name=name, args=self._parse_argument_list(args)
                )
                component_info.methods[name] = method_info

        # Extract arrow functions
        arrow_defs = re.findall(
            r'[\'"]?(\w+)[\'"]?\s*:\s*(async\s+)?\(([^)]*)\)\s*=>', methods_obj
        )
        for name, is_async, args in arrow_defs:
            if name not in component_info.methods:
                method_info = MethodInfo(
                    name=name,
                    args=self._parse_argument_list(args),
                    is_async=bool(is_async),
                )
                component_info.methods[name] = method_info

    def _parse_watch_object(
        self, watch_obj: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse watch object.

        Args:
            watch_obj: The watch object content
            component_info: VueComponentInfo to update
        """
        # Extract simple watchers
        watch_props = re.findall(r'[\'"]?(\w+(?:\.\w+)*)[\'"]?\s*\(', watch_obj)
        for prop in watch_props:
            component_info.watchers[prop] = WatchInfo(
                target=prop, handler=f"{prop}Handler"
            )

        # Extract watchers with options
        watch_options = re.findall(
            r'[\'"]?(\w+(?:\.\w+)*)[\'"]?\s*:\s*{[\s\S]*?handler\s*:[\s\S]*?(?:immediate\s*:\s*(true|false))?[\s\S]*?(?:deep\s*:\s*(true|false))?',
            watch_obj,
        )
        for prop, immediate, deep in watch_options:
            component_info.watchers[prop] = WatchInfo(
                target=prop,
                handler=f"{prop}Handler",
                immediate=immediate == "true",
                deep=deep == "true",
            )

    def _parse_components_object(
        self, components_obj: str, component_info: VueComponentInfo
    ) -> None:
        """
        Parse components object.

        Args:
            components_obj: The components object content
            component_info: VueComponentInfo to update
        """
        # Extract component registrations
        component_entries = re.findall(r'[\'"]?(\w+)[\'"]?\s*:\s*(\w+)', components_obj)
        for local_name, component_ref in component_entries:
            component_info.components[local_name] = component_ref

        # Look for ES6 shorthand notation
        shorthand_entries = re.findall(r"(\w+)(?:,|$)", components_obj)
        for component_name in shorthand_entries:
            if component_name not in component_info.components:
                component_info.components[component_name] = component_name

    def _extract_imports(self, script_content: str) -> List[str]:
        """
        Extract import statements from script content.

        Args:
            script_content: The script content

        Returns:
            List of import statements
        """
        imports = []

        # Extract ES6 imports
        import_matches = re.findall(
            r'import\s+([\s\S]*?)\s+from\s+[\'"]([^\'"]+)[\'"]', script_content
        )
        for what, where in import_matches:
            imports.append(f"import {what} from '{where}'")

        return imports

    def _parse_argument_list(self, args_str: str) -> List[str]:
        """
        Parse function argument list into a list of argument names.

        Args:
            args_str: String containing comma-separated arguments

        Returns:
            List of argument names
        """
        if not args_str.strip():
            return []

        # Split by comma and clean up whitespace
        return [arg.strip() for arg in args_str.split(",")]


class TypeScriptParser:
    """Parser for TypeScript files."""

    def __init__(self) -> None:
        """Initialize the TypeScript parser."""
        pass

    def parse(self, file_path: Path) -> TypeScriptFileInfo:
        """
        Parse a TypeScript file.

        Args:
            file_path: Path to the TypeScript file

        Returns:
            TypeScriptFileInfo object containing file data
        """
        file_name = file_path.stem
        file_info = TypeScriptFileInfo(name=file_name, file_path=file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract imports
            file_info.imports = self._extract_imports(content)

            # Extract exports
            file_info.exports = self._extract_exports(content)

            # Extract type definitions
            file_info.types = self._extract_types(content)

            # Extract functions
            file_info.functions = self._extract_functions(content)

            # Extract classes
            file_info.classes = self._extract_classes(content)

            # Extract constants and variables
            constants, variables = self._extract_variables(content)
            file_info.constants = constants
            file_info.variables = variables

            # Extract file description from leading comment
            description_match = re.search(r"^/\*\*([\s\S]*?)\*/", content)
            if description_match:
                file_info.description = description_match.group(1).strip()

            return file_info

        except Exception as e:
            logger.error(f"Error parsing TypeScript file {file_path}: {str(e)}")
            return file_info

    def _extract_imports(self, content: str) -> List[str]:
        """
        Extract import statements from TypeScript content.

        Args:
            content: The TypeScript file content

        Returns:
            List of import statements
        """
        imports = []

        # Extract regular imports
        import_matches = re.findall(
            r'import\s+([\s\S]*?)\s+from\s+[\'"]([^\'"]+)[\'"];', content
        )
        for what, where in import_matches:
            imports.append(f"import {what} from '{where}'")

        # Extract type imports
        type_import_matches = re.findall(
            r'import\s+type\s+([\s\S]*?)\s+from\s+[\'"]([^\'"]+)[\'"];', content
        )
        for what, where in type_import_matches:
            imports.append(f"import type {what} from '{where}'")

        return imports

    def _extract_exports(self, content: str) -> List[str]:
        """
        Extract export statements from TypeScript content.

        Args:
            content: The TypeScript file content

        Returns:
            List of export statements
        """
        exports = []

        # Extract named exports
        export_matches = re.findall(
            r"export\s+(?:const|let|var|function|class|interface|type|enum)\s+(\w+)",
            content,
        )
        for name in export_matches:
            exports.append(name)

        # Extract default exports
        default_export_match = re.search(
            r"export\s+default\s+(?:const|let|var|function|class|interface|type|enum)?\s*(\w+)",
            content,
        )
        if default_export_match:
            exports.append(f"default: {default_export_match.group(1)}")

        return exports

    def _extract_types(self, content: str) -> Dict[str, TypeInfo]:
        """
        Extract type definitions from TypeScript content.

        Args:
            content: The TypeScript file content

        Returns:
            Dictionary of TypeInfo objects
        """
        types = {}

        # Extract interfaces
        interface_matches = re.findall(
            r"(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\s\S]*?))?\s*{([\s\S]*?)}",
            content,
        )
        for name, extends_str, body in interface_matches:
            extends = []
            if extends_str:
                extends = [ext.strip() for ext in extends_str.split(",")]

            properties = {}
            prop_matches = re.findall(r"(\w+)\??\s*:\s*([^;]+);", body)
            for prop_name, prop_type in prop_matches:
                properties[prop_name.rstrip("?")] = prop_type.strip()

            types[name] = TypeInfo(
                name=name, kind="interface", properties=properties, extends=extends
            )

        # Extract type aliases
        type_alias_matches = re.findall(
            r"(?:export\s+)?type\s+(\w+)(?:<[^>]*>)?\s*=\s*([^;]+);", content
        )
        for name, definition in type_alias_matches:
            types[name] = TypeInfo(
                name=name, kind="type", source_code=definition.strip()
            )

        # Extract enums
        enum_matches = re.findall(r"(?:export\s+)?enum\s+(\w+)\s*{([\s\S]*?)}", content)
        for name, body in enum_matches:
            properties = {}
            enum_values = re.findall(r"(\w+)(?:\s*=\s*([^,]+))?", body)
            for value_name, value in enum_values:
                properties[value_name] = value.strip() if value else "[auto]"

            types[name] = TypeInfo(name=name, kind="enum", properties=properties)

        return types

    def _extract_functions(self, content: str) -> Dict[str, MethodInfo]:
        """
        Extract function definitions from TypeScript content.

        Args:
            content: The TypeScript file content

        Returns:
            Dictionary of MethodInfo objects
        """
        functions = {}

        # Extract regular function declarations
        function_matches = re.findall(
            r"(?:export\s+)?(?:async\s+)?function\s+(\w+)(?:<[^>]*>)?\s*\(([\s\S]*?)\)(?:\s*:\s*([^{]+))?\s*{",
            content,
        )
        for name, args_str, return_type in function_matches:
            args = self._parse_typescript_args(args_str)
            is_async = "async function " + name in content

            functions[name] = MethodInfo(
                name=name,
                args=args,
                return_type=return_type.strip() if return_type else None,
                is_async=is_async,
            )

        # Extract arrow function constants
        arrow_matches = re.findall(
            r"(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(([\s\S]*?)\)(?:\s*:\s*([^=]+))?\s*=>\s*[{(]",
            content,
        )
        for name, args_str, return_type in arrow_matches:
            args = self._parse_typescript_args(args_str)
            is_async = "async " in content[content.find(name) - 30 : content.find(name)]

            functions[name] = MethodInfo(
                name=name,
                args=args,
                return_type=return_type.strip() if return_type else None,
                is_async=is_async,
            )

        return functions

    def _extract_classes(self, content: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract class definitions from TypeScript content.

        Args:
            content: The TypeScript file content

        Returns:
            Dictionary of class information
        """
        classes = {}

        # Extract class declarations
        class_matches = re.findall(
            r"(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\s\S]*?))?\s*{([\s\S]*?)}",
            content,
        )

        for name, extends, implements, body in class_matches:
            class_info = {
                "name": name,
                "extends": extends if extends else None,
                "implements": (
                    [impl.strip() for impl in implements.split(",")]
                    if implements
                    else []
                ),
                "properties": {},
                "methods": {},
                "constructor": None,
            }

            # Extract properties
            property_matches = re.findall(
                r"(private|protected|public|readonly)?\s*(\w+)\s*:\s*([^;]+);", body
            )
            for visibility, prop_name, prop_type in property_matches:
                visibility = visibility or "public"
                class_info["properties"][prop_name] = {
                    "type": prop_type.strip(),
                    "visibility": visibility,
                }

            # Extract methods
            method_matches = re.findall(
                r"(private|protected|public|static|async)?\s*(private|protected|public|static|async)?\s*(\w+)\s*\(([\s\S]*?)\)(?:\s*:\s*([^{]+))?\s*{",
                body,
            )
            for mod1, mod2, method_name, args_str, return_type in method_matches:
                if method_name == "constructor":
                    class_info["constructor"] = {
                        "args": self._parse_typescript_args(args_str)
                    }
                else:
                    modifiers = []
                    if mod1:
                        modifiers.append(mod1)
                    if mod2:
                        modifiers.append(mod2)

                    visibility = "public"
                    is_static = False
                    is_async = False

                    for mod in modifiers:
                        if mod in ["private", "protected", "public"]:
                            visibility = mod
                        elif mod == "static":
                            is_static = True
                        elif mod == "async":
                            is_async = True

                    class_info["methods"][method_name] = {
                        "args": self._parse_typescript_args(args_str),
                        "return_type": return_type.strip() if return_type else None,
                        "visibility": visibility,
                        "is_static": is_static,
                        "is_async": is_async,
                    }

            classes[name] = class_info

        return classes

    def _extract_variables(self, content: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Extract constant and variable declarations from TypeScript content.

        Args:
            content: The TypeScript file content

        Returns:
            Tuple of (constants, variables) dictionaries
        """
        constants = {}
        variables = {}

        # Extract const declarations
        const_matches = re.findall(
            r"(?:export\s+)?const\s+(\w+)(?:\s*:\s*([^=]+))?\s*=\s*([^;]+);", content
        )
        for name, type_str, value in const_matches:
            # Skip if it's a function declaration
            if "=>" in value and "(" in value:
                continue

            if value.strip():
                constants[name] = value.strip()

        # Extract let/var declarations
        var_matches = re.findall(
            r"(?:export\s+)?(?:let|var)\s+(\w+)(?:\s*:\s*([^=]+))?\s*=\s*([^;]+);",
            content,
        )
        for name, type_str, value in var_matches:
            if value.strip():
                variables[name] = value.strip()

        return constants, variables

    def _parse_typescript_args(self, args_str: str) -> List[str]:
        """
        Parse TypeScript function arguments.

        Args:
            args_str: String containing TypeScript function arguments

        Returns:
            List of argument definitions
        """
        if not args_str.strip():
            return []

        # This is a simplified approach that doesn't handle all edge cases
        args = []
        for arg in args_str.split(","):
            arg = arg.strip()
            if arg:
                # Extract parameter name, type, and default value if present
                parts = arg.split(":")
                param_name = parts[0].strip()
                if len(parts) > 1:
                    param_type = parts[1].strip()
                    if "=" in param_name:
                        name_parts = param_name.split("=")
                        param_name = name_parts[0].strip()
                        default_value = name_parts[1].strip()
                        args.append(f"{param_name}: {param_type} = {default_value}")
                    else:
                        args.append(f"{param_name}: {param_type}")
                else:
                    args.append(param_name)

        return args


class FrontendStructureMapper:
    """
    Main class to analyze frontend projects and generate code structure representations.
    """

    def __init__(
        self,
        root_path: Union[str, Path],
        project_name: Optional[str] = None,
        include_templates: bool = False,
        ignore_patterns: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the frontend structure mapper.

        Args:
            root_path: Root directory of the project to analyze
            project_name: Name of the project (default: inferred from directory name)
            include_templates: Whether to include Vue templates in the output
            ignore_patterns: List of regex patterns for files/dirs to ignore
        """
        self.root_path = Path(root_path).resolve()
        self.project_name = project_name or self.root_path.name
        self.include_templates = include_templates
        self.ignore_patterns = ignore_patterns or []
        self.ignore_regexes = [re.compile(pattern) for pattern in self.ignore_patterns]

        # Add common patterns to ignore if not specified
        default_ignores = [
            r"node_modules",
            r"\.git",
            r"dist",
            r"\.vscode",
            r"\.idea",
            r"coverage",
            r"__tests__",
            r"\.nuxt",
            r"\.output",
        ]

        for pattern in default_ignores:
            if not any(re.search(pattern, ignore) for ignore in self.ignore_patterns):
                self.ignore_regexes.append(re.compile(pattern))

        self.vue_parser = VueParser(include_template=include_templates)
        self.typescript_parser = TypeScriptParser()

        self.project_info = FrontendProjectInfo(
            name=self.project_name,
            root_path=self.root_path,
            project_type="Vue 3" if self._is_vue_project() else "Unknown",
        )

        # Read package.json and tsconfig.json if they exist
        self._read_project_config()

    def _should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored based on patterns."""
        str_path = str(path)
        return any(regex.search(str_path) for regex in self.ignore_regexes)

    def _is_vue_project(self) -> bool:
        """Check if this is a Vue project based on package.json."""
        package_json_path = self.root_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    package_data = json.load(f)

                dependencies = package_data.get("dependencies", {})
                dev_dependencies = package_data.get("devDependencies", {})

                return "vue" in dependencies or "vue" in dev_dependencies
            except Exception:
                pass

        # Fallback to checking if src/App.vue exists
        app_vue_path = self.root_path / "src" / "App.vue"
        return app_vue_path.exists()

    def _read_project_config(self) -> None:
        """Read project configuration files."""
        # Read package.json
        package_json_path = self.root_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    self.project_info.package_json = json.load(f)
            except Exception as e:
                logger.error(f"Error reading package.json: {str(e)}")

        # Read tsconfig.json
        tsconfig_path = self.root_path / "tsconfig.json"
        if tsconfig_path.exists():
            try:
                with open(tsconfig_path, "r", encoding="utf-8") as f:
                    self.project_info.tsconfig_json = json.load(f)
            except Exception as e:
                logger.error(f"Error reading tsconfig.json: {str(e)}")

    def analyze_project(self) -> FrontendProjectInfo:
        """
        Analyze the entire project and return the FrontendProjectInfo.

        Returns:
            FrontendProjectInfo object containing the project structure
        """
        logger.info(f"Analyzing frontend project at {self.root_path}")

        # Create the root directory structure
        self.project_info.structure = DirectoryInfo(
            name=self.root_path.name, path=self.root_path
        )

        # Analyze the project structure
        self._analyze_directory(self.root_path, self.project_info.structure)

        return self.project_info

    def _analyze_directory(self, dir_path: Path, dir_info: DirectoryInfo) -> None:
        """
        Analyze a directory recursively.

        Args:
            dir_path: Path to the directory
            dir_info: DirectoryInfo object to populate
        """
        for item in os.scandir(dir_path):
            item_path = Path(item.path)

            if self._should_ignore(item_path):
                continue

            if item.is_dir():
                # Process subdirectory
                subdir_info = DirectoryInfo(name=item.name, path=item_path)
                self._analyze_directory(item_path, subdir_info)
                dir_info.subdirectories[item.name] = subdir_info
            elif item.is_file():
                file_type = self._get_file_type(item_path)

                if file_type == FileType.VUE:
                    # Parse Vue component
                    component_info = self.vue_parser.parse(item_path)
                    dir_info.vue_components[component_info.name] = component_info
                elif file_type in [FileType.TYPESCRIPT, FileType.JAVASCRIPT]:
                    # Parse TypeScript/JavaScript file
                    file_info = self.typescript_parser.parse(item_path)
                    dir_info.typescript_files[file_info.name] = file_info
                else:
                    # Add to other files
                    dir_info.other_files.append(item.name)

    def _get_file_type(self, file_path: Path) -> FileType:
        """
        Determine the file type based on extension.

        Args:
            file_path: Path to the file

        Returns:
            FileType enum value
        """
        extension = file_path.suffix.lower()

        if extension == ".vue":
            return FileType.VUE
        elif extension in [".ts", ".tsx"]:
            return FileType.TYPESCRIPT
        elif extension in [".js", ".jsx"]:
            return FileType.JAVASCRIPT
        elif extension == ".html":
            return FileType.HTML
        elif extension == ".css":
            return FileType.CSS
        elif extension == ".scss":
            return FileType.SCSS
        elif extension == ".json":
            return FileType.JSON
        else:
            return FileType.UNKNOWN

    def export_json(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as JSON.

        Args:
            output_path: Path to save the JSON file (optional)

        Returns:
            JSON string if output_path is None, otherwise None
        """
        # Convert the project info to a dictionary
        project_dict = self._project_info_to_dict()

        # Convert to JSON
        json_str = json.dumps(project_dict, indent=2)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_str)
            logger.info(f"JSON structure written to {output_path}")
            return None
        else:
            return json_str

    def export_markdown(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as Markdown.

        Args:
            output_path: Path to save the Markdown file (optional)

        Returns:
            Markdown string if output_path is None, otherwise None
        """
        md_lines = [
            f"# {self.project_name} Frontend Structure",
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Add project overview
        md_lines.extend(
            [
                "## Project Overview",
                f"- Project Name: {self.project_info.name}",
                f"- Project Type: {self.project_info.project_type}",
                f"- Root Path: {self.project_info.root_path}",
                "",
            ]
        )

        # Add dependencies if available
        if self.project_info.package_json:
            md_lines.append("### Dependencies")
            deps = self.project_info.package_json.get("dependencies", {})
            dev_deps = self.project_info.package_json.get("devDependencies", {})

            if deps:
                md_lines.append("**Production Dependencies:**")
                for dep, version in deps.items():
                    md_lines.append(f"- {dep}: {version}")
                md_lines.append("")

            if dev_deps:
                md_lines.append("**Development Dependencies:**")
                for dep, version in dev_deps.items():
                    md_lines.append(f"- {dep}: {version}")
                md_lines.append("")

        # Add directory structure
        md_lines.extend(
            [
                "## Directory Structure",
                "```",
            ]
        )

        # Generate directory tree
        md_lines.extend(self._generate_directory_tree())
        md_lines.append("```")
        md_lines.append("")

        # Add component structure
        md_lines.append("## Components")

        # Process all Vue components
        components = self._collect_all_components(self.project_info.structure)
        if components:
            for component_name, component_info in sorted(components.items()):
                md_lines.extend(self._component_to_markdown(component_info))
        else:
            md_lines.append("No Vue components found.")
            md_lines.append("")

        # Add TypeScript types/interfaces
        md_lines.append("## TypeScript Types")

        # Process all TypeScript files
        ts_files = self._collect_all_typescript_files(self.project_info.structure)
        if ts_files:
            for file_name, file_info in sorted(ts_files.items()):
                if file_info.types:
                    md_lines.extend(self._typescript_types_to_markdown(file_info))
        else:
            md_lines.append("No TypeScript types found.")
            md_lines.append("")

        # Add utility functions
        md_lines.append("## Utility Functions")

        # Process all utility functions from TypeScript files
        if ts_files:
            functions_found = False
            for file_name, file_info in sorted(ts_files.items()):
                if file_info.functions:
                    functions_found = True
                    md_lines.extend(self._typescript_functions_to_markdown(file_info))

            if not functions_found:
                md_lines.append("No utility functions found.")
                md_lines.append("")
        else:
            md_lines.append("No utility functions found.")
            md_lines.append("")

        # Join all lines
        markdown_str = "\n".join(md_lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_str)
            logger.info(f"Markdown structure written to {output_path}")
            return None
        else:
            return markdown_str

    def export_mermaid(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as a Mermaid diagram.

        Args:
            output_path: Path to save the Mermaid file (optional)

        Returns:
            Mermaid string if output_path is None, otherwise None
        """
        mermaid_lines = ["classDiagram"]

        # Generate class definitions for components and their relationships
        components = self._collect_all_components(self.project_info.structure)
        ts_files = self._collect_all_typescript_files(self.project_info.structure)

        # Add components as classes
        for component_name, component_info in components.items():
            mermaid_lines.append(f"  class {component_name}")

            # Add component props as attributes
            for prop_name, prop_info in component_info.props.items():
                prop_type = prop_info.type or "any"
                required = "*" if prop_info.required else ""
                mermaid_lines.append(
                    f"  {component_name} : +{prop_name}{required} : {prop_type}"
                )

            # Add component emits as methods
            for emit_name, emit_info in component_info.emits.items():
                payload = (
                    f"({emit_info.payload_type})" if emit_info.payload_type else "()"
                )
                mermaid_lines.append(f"  {component_name} : +emit_{emit_name}{payload}")

            # Add computed properties
            for computed_name, computed_info in component_info.computed.items():
                return_type = computed_info.return_type or "any"
                mermaid_lines.append(
                    f"  {component_name} : +{computed_name} : {return_type}"
                )

            # Add methods
            for method_name, method_info in component_info.methods.items():
                args = ", ".join(method_info.args)
                return_type = method_info.return_type or "void"
                mermaid_lines.append(
                    f"  {component_name} : +{method_name}({args}) : {return_type}"
                )

        # Add relationships (component imports)
        component_relationships = set()
        for component_name, component_info in components.items():
            for imported_component in component_info.components.values():
                if imported_component in components:
                    component_relationships.add(
                        f"  {imported_component} <-- {component_name} : imports"
                    )

        # Add all relationships
        for relationship in component_relationships:
            mermaid_lines.append(relationship)

        # Add TypeScript types and their relationships
        for file_name, file_info in ts_files.items():
            for type_name, type_info in file_info.types.items():
                qualified_name = f"{file_name}.{type_name}"
                mermaid_lines.append(f"  class {qualified_name}")

                # Add type properties
                for prop_name, prop_type in type_info.properties.items():
                    mermaid_lines.append(
                        f"  {qualified_name} : +{prop_name} : {prop_type}"
                    )

                # Add inheritance relationships
                for extends_type in type_info.extends:
                    if "." not in extends_type:
                        # Check if it's defined in the same file
                        if extends_type in file_info.types:
                            extends_qualified = f"{file_name}.{extends_type}"
                            mermaid_lines.append(
                                f"  {extends_qualified} <|-- {qualified_name} : extends"
                            )
                    else:
                        mermaid_lines.append(
                            f"  {extends_type} <|-- {qualified_name} : extends"
                        )

        # Join all lines
        mermaid_str = "\n".join(mermaid_lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(mermaid_str)
            logger.info(f"Mermaid diagram written to {output_path}")
            return None
        else:
            return mermaid_str

    def export_text(self, output_path: Optional[Path] = None) -> Optional[str]:
        """
        Export the project structure as plain text.

        Args:
            output_path: Path to save the text file (optional)

        Returns:
            Text string if output_path is None, otherwise None
        """
        lines = [
            f"{self.project_name} Frontend Structure",
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Project overview
        lines.append("Project Overview:")
        lines.append(f"  Project Name: {self.project_info.name}")
        lines.append(f"  Project Type: {self.project_info.project_type}")
        lines.append(f"  Root Path: {self.project_info.root_path}")
        lines.append("")

        # Directory structure
        lines.append("Directory Structure:")
        lines.extend(self._generate_directory_tree())
        lines.append("")

        # Components
        lines.append("Components:")
        components = self._collect_all_components(self.project_info.structure)
        if components:
            for component_name, component_info in sorted(components.items()):
                rel_path = component_info.file_path.relative_to(
                    self.project_info.root_path
                )
                lines.append(f"  {component_name} ({rel_path}):")
                lines.append(f"    Type: {component_info.component_type}")

                if component_info.props:
                    lines.append("    Props:")
                    for prop_name, prop_info in component_info.props.items():
                        prop_type = f": {prop_info.type}" if prop_info.type else ""
                        required = " (required)" if prop_info.required else ""
                        lines.append(f"      {prop_name}{prop_type}{required}")

                if component_info.emits:
                    lines.append("    Emits:")
                    for emit_name, emit_info in component_info.emits.items():
                        payload = (
                            f": {emit_info.payload_type}"
                            if emit_info.payload_type
                            else ""
                        )
                        lines.append(f"      {emit_name}{payload}")

                if component_info.computed:
                    lines.append("    Computed:")
                    for computed_name in component_info.computed:
                        lines.append(f"      {computed_name}")

                if component_info.methods:
                    lines.append("    Methods:")
                    for method_name, method_info in component_info.methods.items():
                        args = ", ".join(method_info.args)
                        is_async = "async " if method_info.is_async else ""
                        lines.append(f"      {is_async}{method_name}({args})")

                if component_info.components:
                    lines.append("    Used Components:")
                    for local_name, component_ref in component_info.components.items():
                        lines.append(f"      {local_name} ({component_ref})")

                lines.append("")
        else:
            lines.append("  No Vue components found.")
            lines.append("")

        # TypeScript Types
        lines.append("TypeScript Types:")
        ts_files = self._collect_all_typescript_files(self.project_info.structure)
        types_found = False

        if ts_files:
            for file_name, file_info in sorted(ts_files.items()):
                if file_info.types:
                    types_found = True
                    rel_path = file_info.file_path.relative_to(
                        self.project_info.root_path
                    )
                    lines.append(f"  {file_name} ({rel_path}):")

                    for type_name, type_info in file_info.types.items():
                        extends = (
                            f" extends {', '.join(type_info.extends)}"
                            if type_info.extends
                            else ""
                        )
                        lines.append(f"    {type_info.kind} {type_name}{extends}")

                        if type_info.properties:
                            lines.append("      Properties:")
                            for prop_name, prop_type in type_info.properties.items():
                                lines.append(f"        {prop_name}: {prop_type}")

                        lines.append("")

        if not types_found:
            lines.append("  No TypeScript types found.")
            lines.append("")

        # Join all lines
        text_str = "\n".join(lines)

        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text_str)
            logger.info(f"Text structure written to {output_path}")
            return None
        else:
            return text_str

    def _project_info_to_dict(self) -> Dict[str, Any]:
        """
        Convert FrontendProjectInfo to a dictionary for JSON serialization.

        Returns:
            Dictionary representation of the project
        """
        project_dict = {
            "name": self.project_info.name,
            "root_path": str(self.project_info.root_path),
            "project_type": self.project_info.project_type,
            "package_json": self.project_info.package_json,
            "tsconfig_json": self.project_info.tsconfig_json,
            "structure": self._directory_info_to_dict(self.project_info.structure),
        }

        return project_dict

    def _directory_info_to_dict(self, dir_info: DirectoryInfo) -> Dict[str, Any]:
        """
        Convert DirectoryInfo to a dictionary for JSON serialization.

        Args:
            dir_info: DirectoryInfo object to convert

        Returns:
            Dictionary representation of the directory
        """
        dir_dict = {
            "name": dir_info.name,
            "path": str(dir_info.path),
            "vue_components": {},
            "typescript_files": {},
            "subdirectories": {},
            "other_files": dir_info.other_files,
        }

        # Convert Vue components
        for component_name, component_info in dir_info.vue_components.items():
            dir_dict["vue_components"][component_name] = self._component_info_to_dict(
                component_info
            )

        # Convert TypeScript files
        for file_name, file_info in dir_info.typescript_files.items():
            dir_dict["typescript_files"][file_name] = (
                self._typescript_file_info_to_dict(file_info)
            )

        # Convert subdirectories
        for subdir_name, subdir_info in dir_info.subdirectories.items():
            dir_dict["subdirectories"][subdir_name] = self._directory_info_to_dict(
                subdir_info
            )

        return dir_dict

    def _component_info_to_dict(
        self, component_info: VueComponentInfo
    ) -> Dict[str, Any]:
        """
        Convert VueComponentInfo to a dictionary for JSON serialization.

        Args:
            component_info: VueComponentInfo object to convert

        Returns:
            Dictionary representation of the component
        """
        component_dict = {
            "name": component_info.name,
            "file_path": str(component_info.file_path),
            "component_type": component_info.component_type,
            "template": component_info.template,
            "props": {},
            "emits": {},
            "data": component_info.data,
            "computed": {},
            "methods": {},
            "watchers": {},
            "hooks": {},
            "imports": component_info.imports,
            "refs": component_info.refs,
            "reactive_state": component_info.reactive_state,
            "provide": component_info.provide,
            "inject": component_info.inject,
            "components": component_info.components,
            "setup_return": component_info.setup_return,
            "directives": component_info.directives,
            "mixins": component_info.mixins,
            "description": component_info.description,
        }

        # Convert props
        for prop_name, prop_info in component_info.props.items():
            component_dict["props"][prop_name] = {
                "name": prop_info.name,
                "type": prop_info.type,
                "required": prop_info.required,
                "default_value": prop_info.default_value,
                "validator": prop_info.validator,
                "description": prop_info.description,
            }

        # Convert emits
        for emit_name, emit_info in component_info.emits.items():
            component_dict["emits"][emit_name] = {
                "name": emit_info.name,
                "payload_type": emit_info.payload_type,
                "description": emit_info.description,
            }

        # Convert computed properties
        for computed_name, computed_info in component_info.computed.items():
            component_dict["computed"][computed_name] = {
                "name": computed_info.name,
                "return_type": computed_info.return_type,
                "description": computed_info.description,
                "getter": computed_info.getter,
                "setter": computed_info.setter,
            }

        # Convert methods
        for method_name, method_info in component_info.methods.items():
            component_dict["methods"][method_name] = {
                "name": method_info.name,
                "args": method_info.args,
                "return_type": method_info.return_type,
                "description": method_info.description,
                "is_async": method_info.is_async,
                "source_code": method_info.source_code,
                "arg_types": method_info.arg_types,
            }

        # Convert watchers
        for watcher_target, watcher_info in component_info.watchers.items():
            component_dict["watchers"][watcher_target] = {
                "target": watcher_info.target,
                "handler": watcher_info.handler,
                "immediate": watcher_info.immediate,
                "deep": watcher_info.deep,
            }

        # Convert hooks
        for hook_name, hook_info in component_info.hooks.items():
            component_dict["hooks"][hook_name] = {
                "name": hook_info.name,
                "source_code": hook_info.source_code,
            }

        return component_dict

    def _typescript_file_info_to_dict(
        self, file_info: TypeScriptFileInfo
    ) -> Dict[str, Any]:
        """
        Convert TypeScriptFileInfo to a dictionary for JSON serialization.

        Args:
            file_info: TypeScriptFileInfo object to convert

        Returns:
            Dictionary representation of the TypeScript file
        """
        file_dict = {
            "name": file_info.name,
            "file_path": str(file_info.file_path),
            "imports": file_info.imports,
            "exports": file_info.exports,
            "types": {},
            "functions": {},
            "classes": file_info.classes,
            "constants": file_info.constants,
            "variables": file_info.variables,
            "description": file_info.description,
        }

        # Convert types
        for type_name, type_info in file_info.types.items():
            file_dict["types"][type_name] = {
                "name": type_info.name,
                "kind": type_info.kind,
                "properties": type_info.properties,
                "extends": type_info.extends,
                "description": type_info.description,
                "source_code": type_info.source_code,
            }

        # Convert functions
        for func_name, func_info in file_info.functions.items():
            file_dict["functions"][func_name] = {
                "name": func_info.name,
                "args": func_info.args,
                "return_type": func_info.return_type,
                "description": func_info.description,
                "is_async": func_info.is_async,
                "source_code": func_info.source_code,
                "arg_types": func_info.arg_types,
            }

        return file_dict

    def _generate_directory_tree(self) -> List[str]:
        """
        Generate a text tree representation of the project's directory structure.

        Returns:
            List of lines representing the directory tree
        """
        lines = [f"{self.project_info.root_path.name}/"]

        # Helper function to recursively build the tree
        def build_tree(path: Path, prefix: str = "", is_last: bool = True) -> List[str]:
            tree_lines = []
            items = list(os.scandir(path))

            # Filter out ignored items
            items = [item for item in items if not self._should_ignore(Path(item.path))]

            # Sort items: directories first, then files
            items.sort(key=lambda x: (not x.is_dir(), x.name))

            for i, item in enumerate(items):
                is_last_item = i == len(items) - 1
                item_prefix = prefix + ("└── " if is_last_item else "├── ")
                next_prefix = prefix + ("    " if is_last_item else "│   ")

                tree_lines.append(
                    f"{item_prefix}{item.name}{os.sep if item.is_dir() else ''}"
                )

                if item.is_dir():
                    tree_lines.extend(
                        build_tree(Path(item.path), next_prefix, is_last_item)
                    )

            return tree_lines

        lines.extend(build_tree(self.project_info.root_path))
        return lines

    def _collect_all_components(
        self, dir_info: DirectoryInfo
    ) -> Dict[str, VueComponentInfo]:
        """
        Collect all Vue components from the project structure.

        Args:
            dir_info: DirectoryInfo object to start from

        Returns:
            Dictionary of component name to VueComponentInfo
        """
        all_components = {}

        # Add components from current directory
        all_components.update(dir_info.vue_components)

        # Recursively add components from subdirectories
        for subdir_info in dir_info.subdirectories.values():
            all_components.update(self._collect_all_components(subdir_info))

        return all_components

    def _collect_all_typescript_files(
        self, dir_info: DirectoryInfo
    ) -> Dict[str, TypeScriptFileInfo]:
        """
        Collect all TypeScript files from the project structure.

        Args:
            dir_info: DirectoryInfo object to start from

        Returns:
            Dictionary of file name to TypeScriptFileInfo
        """
        all_files = {}

        # Add files from current directory
        all_files.update(dir_info.typescript_files)

        # Recursively add files from subdirectories
        for subdir_info in dir_info.subdirectories.values():
            all_files.update(self._collect_all_typescript_files(subdir_info))

        return all_files

    def _component_to_markdown(self, component_info: VueComponentInfo) -> List[str]:
        """
        Convert a Vue component to Markdown.

        Args:
            component_info: VueComponentInfo to convert

        Returns:
            List of Markdown lines
        """
        rel_path = component_info.file_path.relative_to(self.project_info.root_path)
        lines = [
            f"### {component_info.name}",
            f"**Path:** `{rel_path}`",
            f"**Type:** {component_info.component_type}",
            "",
        ]

        # Props
        if component_info.props:
            lines.append("#### Props")
            lines.append("| Prop | Type | Required | Default |")
            lines.append("| ---- | ---- | -------- | ------- |")

            for prop_name, prop_info in sorted(component_info.props.items()):
                prop_type = prop_info.type or "Any"
                required = "Yes" if prop_info.required else "No"
                default_value = prop_info.default_value or "-"
                lines.append(
                    f"| {prop_name} | {prop_type} | {required} | {default_value} |"
                )

            lines.append("")

        # Emits
        if component_info.emits:
            lines.append("#### Emits")
            lines.append("| Event | Payload |")
            lines.append("| ----- | ------- |")

            for emit_name, emit_info in sorted(component_info.emits.items()):
                payload = emit_info.payload_type or "-"
                lines.append(f"| {emit_name} | {payload} |")

            lines.append("")

        # Data (Options API) or Refs (Composition API)
        if component_info.component_type == "Options API" and component_info.data:
            lines.append("#### Data Properties")
            for data_name, data_value in sorted(component_info.data.items()):
                lines.append(f"- `{data_name}`: {data_value}")
            lines.append("")
        elif component_info.component_type.startswith("Composition API") and (
            component_info.refs or component_info.reactive_state
        ):
            lines.append("#### Reactive State")

            if component_info.refs:
                lines.append("**Refs:**")
                for ref_name, ref_value in sorted(component_info.refs.items()):
                    lines.append(f"- `{ref_name}`: {ref_value}")
                lines.append("")

            if component_info.reactive_state:
                lines.append("**Reactive Objects:**")
                for state_name, state_value in sorted(
                    component_info.reactive_state.items()
                ):
                    lines.append(f"- `{state_name}`: {state_value}")
                lines.append("")

        # Computed Properties
        if component_info.computed:
            lines.append("#### Computed Properties")

            for computed_name, computed_info in sorted(component_info.computed.items()):
                setter = " (with setter)" if computed_info.setter else ""
                lines.append(f"- `{computed_name}`{setter}")

            lines.append("")

        # Methods
        if component_info.methods:
            lines.append("#### Methods")

            for method_name, method_info in sorted(component_info.methods.items()):
                is_async = "async " if method_info.is_async else ""
                args = ", ".join(method_info.args)
                return_type = (
                    f" → {method_info.return_type}" if method_info.return_type else ""
                )
                lines.append(f"- `{is_async}{method_name}({args}){return_type}`")

            lines.append("")

        # Watchers
        if component_info.watchers:
            lines.append("#### Watchers")

            for target, watcher_info in sorted(component_info.watchers.items()):
                options = []
                if watcher_info.immediate:
                    options.append("immediate")
                if watcher_info.deep:
                    options.append("deep")

                options_str = f" ({', '.join(options)})" if options else ""
                lines.append(f"- `{target}`{options_str}")

            lines.append("")

        # Lifecycle Hooks
        if component_info.hooks:
            lines.append("#### Lifecycle Hooks")

            for hook_name in sorted(component_info.hooks.keys()):
                lines.append(f"- `{hook_name}`")

            lines.append("")

        # Dependencies
        sections = []

        if component_info.components:
            sections.append(
                (
                    "Components",
                    [f"`{k}` ({v})" for k, v in component_info.components.items()],
                )
            )

        if component_info.provide:
            sections.append(
                ("Provided Keys", [f"`{key}`" for key in component_info.provide])
            )

        if component_info.inject:
            sections.append(
                ("Injected Keys", [f"`{key}`" for key in component_info.inject])
            )

        if component_info.directives:
            sections.append(
                (
                    "Directives",
                    [f"`{directive}`" for directive in component_info.directives],
                )
            )

        if component_info.mixins:
            sections.append(
                ("Mixins", [f"`{mixin}`" for mixin in component_info.mixins])
            )

        if sections:
            lines.append("#### Dependencies")

            for section_name, items in sections:
                if items:
                    lines.append(f"**{section_name}:**")
                    lines.extend([f"- {item}" for item in sorted(items)])
                    lines.append("")

        return lines

    def _typescript_types_to_markdown(self, file_info: TypeScriptFileInfo) -> List[str]:
        """
        Convert TypeScript types to Markdown.

        Args:
            file_info: TypeScriptFileInfo containing types

        Returns:
            List of Markdown lines
        """
        rel_path = file_info.file_path.relative_to(self.project_info.root_path)
        lines = [f"### {file_info.name}", f"**Path:** `{rel_path}`", ""]

        for type_name, type_info in sorted(file_info.types.items()):
            kind = type_info.kind.capitalize()
            extends_str = (
                f" extends {', '.join(type_info.extends)}" if type_info.extends else ""
            )

            lines.append(f"#### {kind}: `{type_name}`{extends_str}")

            if type_info.properties:
                lines.append("| Property | Type |")
                lines.append("| -------- | ---- |")

                for prop_name, prop_type in sorted(type_info.properties.items()):
                    lines.append(f"| {prop_name} | {prop_type} |")
            elif type_info.source_code:
                lines.append("```typescript")
                lines.append(f"type {type_name} = {type_info.source_code}")
                lines.append("```")

            lines.append("")

        return lines

    def _typescript_functions_to_markdown(
        self, file_info: TypeScriptFileInfo
    ) -> List[str]:
        """
        Convert TypeScript functions to Markdown.

        Args:
            file_info: TypeScriptFileInfo containing functions

        Returns:
            List of Markdown lines
        """
        if not file_info.functions:
            return []

        rel_path = file_info.file_path.relative_to(self.project_info.root_path)
        lines = [f"### {file_info.name}", f"**Path:** `{rel_path}`", ""]

        for func_name, func_info in sorted(file_info.functions.items()):
            is_async = "async " if func_info.is_async else ""
            args = ", ".join(func_info.args)
            return_type = f" → {func_info.return_type}" if func_info.return_type else ""

            lines.append(f"#### Function: `{is_async}{func_name}({args}){return_type}`")

            if func_info.description:
                lines.append(func_info.description)

            lines.append("")

        return lines


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive frontend structure maps for Vue 3 + TypeScript projects"
    )
    parser.add_argument("input", help="Input directory to analyze")
    parser.add_argument("--output", help="Output file (default: standard output)")
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "mermaid", "text"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument("--project-name", help="Project name (default: directory name)")
    parser.add_argument(
        "--include-templates",
        action="store_true",
        help="Include Vue templates in the output",
    )
    parser.add_argument("--ignore", help="Comma-separated list of patterns to ignore")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Parse ignore patterns
    ignore_patterns = []
    if args.ignore:
        ignore_patterns = [pattern.strip() for pattern in args.ignore.split(",")]

    # Create the mapper
    mapper = FrontendStructureMapper(
        root_path=args.input,
        project_name=args.project_name,
        include_templates=args.include_templates,
        ignore_patterns=ignore_patterns,
    )

    # Analyze the project
    mapper.analyze_project()

    # Export in the requested format
    output_path = Path(args.output) if args.output else None

    if args.format == "json":
        result = mapper.export_json(output_path)
    elif args.format == "markdown":
        result = mapper.export_markdown(output_path)
    elif args.format == "mermaid":
        result = mapper.export_mermaid(output_path)
    elif args.format == "text":
        result = mapper.export_text(output_path)
    else:
        parser.error(f"Unsupported format: {args.format}")
        return

    # Print to stdout if no output file specified
    if result:
        print(result)


if __name__ == "__main__":
    main()
