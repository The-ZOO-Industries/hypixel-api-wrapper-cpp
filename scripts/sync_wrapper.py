"""Refresh include/hypixel.hpp from the latest HypixelTracking snapshots.

Downloads the per-endpoint JSON samples and regenerates the single-header wrapper.
Intended to be run periodically (see .github/workflows/sync-wrapper.yml).
"""
from __future__ import annotations

import os
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen import generate, parse_func


# (HypixelTracking type name, generated root class name)
# Order matches the layout in include/hypixel.hpp.
ENDPOINTS = [
    ('player', 'PlayerResponse'),
    ('achievements', 'AchievementsResponse'),
    ('challenges', 'ChallengesResponse'),
    ('companions', 'CompanionsResponse'),
    ('games', 'GamesResponse'),
    ('guild', 'GuildResponse'),
    ('guild_achievements', 'GuildAchievementsResponse'),
    ('guild_permissions', 'GuildPermissionsResponse'),
    ('pets', 'PetsResponse'),
    ('quests', 'QuestsResponse'),
    ('skyblock_profile_v2', 'SkyblockProfileV2Response'),
    ('skyblock_garden', 'SkyblockGardenResponse'),
    ('skyblock_bazaar_products', 'SkyblockBazaarProductsResponse'),
    ('skyblock_collections', 'SkyblockCollectionsResponse'),
    ('skyblock_skills', 'SkyblockSkillsResponse'),
    ('skyblock_items', 'SkyblockItemsResponse'),
]

UPSTREAM = 'https://raw.githubusercontent.com/HypixelDatabase/HypixelTracking/master/API/{name}.json'

HEADER = '''#pragma once

// Generated from HypixelDatabase/HypixelTracking API JSON samples by scripts/sync_wrapper.py.
// Single-header wrapper for player, achievements, challenges, companions, games, guild,
// guild achievements, guild permissions, pets, quests, skyblock profile v2, skyblock garden,
// skyblock bazaar products, skyblock collections, skyblock skills, and skyblock items responses.

#include <optional>
#include <string>
#include <string_view>
#include <utility>
#include <nlohmann/json.hpp>

namespace hypixel {

class JsonView {
public:
  using json = nlohmann::json;
  JsonView() = default;
  explicit JsonView(const json* value) : value_(value) {}
  [[nodiscard]] bool exists() const noexcept { return value_ != nullptr && !value_->is_null(); }
  [[nodiscard]] explicit operator bool() const noexcept { return exists(); }
  [[nodiscard]] const json& raw() const { static const json null_json{}; return value_ ? *value_ : null_json; }
  [[nodiscard]] bool contains(std::string_view key) const { return value_ && value_->is_object() && value_->contains(std::string(key)); }
  [[nodiscard]] JsonView at(std::string_view key) const {
    if (!value_ || !value_->is_object()) return JsonView{};
    auto it = value_->find(std::string(key));
    return it == value_->end() ? JsonView{} : JsonView{&*it};
  }
  template <class T> [[nodiscard]] std::optional<T> get() const {
    if (!exists()) return std::nullopt;
    try { return value_->get<T>(); } catch (...) { return std::nullopt; }
  }
  template <class T> [[nodiscard]] T value_or(T fallback) const {
    auto parsed = get<T>();
    return parsed ? std::move(*parsed) : fallback;
  }
protected:
  template <class T> [[nodiscard]] T object_at(std::string_view key) const {
    auto child = at(key);
    return T{child.exists() ? &child.raw() : nullptr};
  }
  const json* value_ = nullptr;
};

'''


def download_all(target_dir: Path) -> None:
    for name, _ in ENDPOINTS:
        url = UPSTREAM.format(name=name)
        out = target_dir / f'{name}.json'
        sys.stderr.write(f'downloading {name}\n')
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
        out.write_bytes(data)


def build_header(samples_dir: Path) -> str:
    forwards_blocks = []
    defs_blocks = []
    parsers = []
    for type_name, root_class in ENDPOINTS:
        sys.stderr.write(f'generating {type_name}\n')
        fwd, defs = generate(root_class, str(samples_dir / f'{type_name}.json'))
        forwards_blocks.append(fwd)
        defs_blocks.append(defs)
        parsers.append(parse_func(root_class, type_name))

    parts = [HEADER]
    parts.append('\n'.join(forwards_blocks))
    parts.append('\n\n')
    parts.append('\n\n'.join(defs_blocks))
    parts.append('\n\n')
    parts.append('\n'.join(parsers))
    parts.append('\n\n} // namespace hypixel\n')
    return ''.join(parts)


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    out_path = repo_root / 'include' / 'hypixel.hpp'

    with tempfile.TemporaryDirectory() as td:
        samples_dir = Path(td)
        download_all(samples_dir)
        content = build_header(samples_dir)

    out_path.write_text(content, encoding='utf-8', newline='\n')
    sys.stderr.write(f'wrote {out_path} ({len(content):,} bytes)\n')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
