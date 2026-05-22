"""Generate C++ wrapper classes from a Hypixel API JSON sample.

Mirrors include/hypixel.hpp style:
- One class per object path. Class name = <RootClass> + PascalCase concat of path segments.
- Method names match the JSON key, with non-identifier characters replaced by `_`.
- C++ keywords get a trailing `_`.
- Sibling collisions after sanitization get `_2`, `_3`, ... suffixes on both method name and child class name,
  with a `// JSON key: <raw>` comment so the original key stays visible.
- Object fields use `object_at<T>` first, then scalar/array fields use `at(key)`.
- Classes emitted in post-order (children before parents).
"""
from __future__ import annotations

import json
import re

CPP_KEYWORDS = {
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'auto', 'bitand', 'bitor', 'bool',
    'break', 'case', 'catch', 'char', 'char8_t', 'char16_t', 'char32_t', 'class', 'compl',
    'concept', 'const', 'consteval', 'constexpr', 'constinit', 'const_cast', 'continue',
    'co_await', 'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do', 'double',
    'dynamic_cast', 'else', 'enum', 'explicit', 'export', 'extern', 'false', 'float',
    'for', 'friend', 'goto', 'if', 'inline', 'int', 'long', 'mutable', 'namespace', 'new',
    'noexcept', 'not', 'not_eq', 'nullptr', 'operator', 'or', 'or_eq', 'private',
    'protected', 'public', 'register', 'reinterpret_cast', 'requires', 'return', 'short',
    'signed', 'sizeof', 'static', 'static_assert', 'static_cast', 'struct', 'switch',
    'template', 'this', 'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid',
    'typename', 'union', 'unsigned', 'using', 'virtual', 'void', 'volatile', 'wchar_t',
    'while', 'xor', 'xor_eq',
}


def pascal_segment(key: str) -> str:
    parts = re.split(r'[^A-Za-z0-9]+', key)
    return ''.join((p[:1].upper() + p[1:]) for p in parts if p)


def method_name(key: str) -> str:
    name = re.sub(r'[^A-Za-z0-9_]', '_', key)
    if not name:
        return ''
    if name[0].isdigit():
        name = '_' + name
    if name in CPP_KEYWORDS:
        name = name + '_'
    return name


def walk(obj, class_name: str, classes: list, seen: set) -> None:
    if class_name in seen:
        return
    seen.add(class_name)

    typed_fields: list[tuple[str, str, str, bool]] = []
    scalar_fields: list[tuple[str, str, bool]] = []
    method_counts: dict[str, int] = {}

    if isinstance(obj, dict):
        for raw_key, value in obj.items():
            base = method_name(raw_key)
            if not base:
                continue
            count = method_counts.get(base, 0) + 1
            method_counts[base] = count
            m = base if count == 1 else f'{base}_{count}'
            with_comment = count > 1
            if isinstance(value, dict):
                child_base = class_name + pascal_segment(raw_key)
                child_name = child_base if count == 1 else f'{child_base}{count}'
                walk(value, child_name, classes, seen)
                typed_fields.append((m, child_name, raw_key, with_comment))
            else:
                scalar_fields.append((m, raw_key, with_comment))

    classes.append((class_name, typed_fields, scalar_fields))


def emit_class(class_name: str, typed_fields, scalar_fields) -> str:
    lines = [f'class {class_name} : public JsonView {{', 'public:', '  using JsonView::JsonView;', '']
    for m, child, raw, with_comment in typed_fields:
        comment = f' // JSON key: {raw}' if with_comment else ''
        lines.append(f'  [[nodiscard]] {child} {m}() const {{ return object_at<{child}>("{raw}"); }}{comment}')
    if typed_fields and scalar_fields:
        lines.append('')
    for m, raw, with_comment in scalar_fields:
        comment = f' // JSON key: {raw}' if with_comment else ''
        lines.append(f'  [[nodiscard]] JsonView {m}() const {{ return at("{raw}"); }}{comment}')
    lines.append('};')
    return '\n'.join(lines)


def generate(root_class: str, sample_path: str) -> tuple[str, str]:
    with open(sample_path, encoding='utf-8') as fp:
        data = json.load(fp)

    classes: list = []
    seen: set[str] = set()
    walk(data if isinstance(data, dict) else {}, root_class, classes, seen)

    forwards = '\n'.join(f'class {c[0]};' for c in classes)
    defs = '\n\n'.join(emit_class(c[0], c[1], c[2]) for c in classes)
    return forwards, defs


def parse_func(root_class: str, type_name: str) -> str:
    return f'inline {root_class} parse_{type_name}_response(const nlohmann::json& json) {{ return {root_class}{{&json}}; }}'
