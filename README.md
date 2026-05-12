# hypixel-player-cpp

Header-only C++ wrapper for the Hypixel player API JSON shape tracked by
[HypixelDatabase/HypixelTracking](https://github.com/HypixelDatabase/HypixelTracking/blob/master/API/player.json).

The wrapper keeps the original JSON available while adding typed nested accessors:

```cpp
#include <hypixel/player.hpp>
#include <nlohmann/json.hpp>

nlohmann::json response = /* API response */;
auto api = hypixel::parse_player_response(response);

auto skywars = api.player().stats().SkyWars();
double xp = skywars.skywars_experience().value_or(0.0);
```

## Dependency

This header requires [nlohmann/json](https://github.com/nlohmann/json).

With CMake, install or vendor `nlohmann_json`, then add this repository's `include`
directory to your target.

## Notes

- Accessors return lightweight views into the original `nlohmann::json`; keep the JSON object alive while using them.
- Missing or mismatched scalar values return `std::nullopt` from `.get<T>()`.
- Use `.value_or(default_value)` for fallback values.
- Use `.raw()` when you need direct access to the underlying JSON field.
