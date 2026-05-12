# hypixel-cpp

Single-header C++ wrapper for Hypixel API JSON shapes tracked by
[HypixelDatabase/HypixelTracking](https://github.com/HypixelDatabase/HypixelTracking/tree/master/API).

The wrapper keeps the original JSON available while adding typed nested accessors.
`nlohmann/json` is vendored in `include/nlohmann`.

```cpp
#include <hypixel.hpp>

nlohmann::json response = /* API response */;
auto api = hypixel::parse_player_response(response);

auto skywars = api.player().stats().SkyWars();
double xp = skywars.skywars_experience().value_or(0.0);
```

## Supported Wrappers

- `parse_player_response`
- `parse_achievements_response`
- `parse_challenges_response`
- `parse_companions_response`
- `parse_games_response`
- `parse_guild_response`
- `parse_guild_achievements_response`
- `parse_guild_permissions_response`
- `parse_pets_response`
- `parse_quests_response`

## Notes

- Accessors return lightweight views into the original `nlohmann::json`; keep the JSON object alive while using them.
- Missing or mismatched scalar values return `std::nullopt` from `.get<T>()`.
- Use `.value_or(default_value)` for fallback values.
- Use `.raw()` when you need direct access to the underlying JSON field.
