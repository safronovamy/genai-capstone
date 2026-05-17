# Weather Rules

---

[RULE_CATEGORY]
[WEATHER]
[TRAVEL_DOMAIN: rainy_weather]

## Rain Adaptation Rules

[CONDITION]
rain_expected

[RULES]

- Prioritize indoor attractions such as museums, aquariums, indoor playgrounds, galleries, cafes, and covered markets.
- Reduce exposed outdoor walking routes.
- Avoid weather-sensitive viewpoints and long outdoor queues.
- Keep indoor backup attractions available near the current district.

[ITINERARY_BEHAVIOR]

- Replace weather-sensitive attractions with indoor alternatives.
- Increase itinerary flexibility during rainy conditions.
- Reduce long transportation-heavy schedules during heavy rain.

---

[RULE_CATEGORY]
[WEATHER]
[TRAVEL_DOMAIN: heat_management]

## High Temperature Rules

[CONDITION]
temperature_high OR extreme_heat

[RULES]

- Avoid long outdoor walks during midday heat.
- Prioritize shaded parks, beaches, riverside areas, cafes, and indoor museums.
- Increase hydration and recovery opportunities.
- Reduce attraction density during the hottest hours.

[ITINERARY_BEHAVIOR]

- Schedule outdoor activities during morning or evening hours.
- Use indoor attractions as midday recovery anchors.

---

[RULE_CATEGORY]
[WEATHER]
[TRAVEL_DOMAIN: cold_weather]

## Cold and Windy Weather Rules

[CONDITION]
cold_weather OR strong_wind

[RULES]

- Keep outdoor activities shorter during cold or windy weather.
- Add warm indoor recovery opportunities between attractions.
- Avoid long exposed walking routes.
- Reduce waiting-heavy outdoor activities.

[ITINERARY_BEHAVIOR]

- Prioritize museums, cafes, aquariums, and indoor attractions.
- Organize compact district-based itineraries.

---

[RULE_CATEGORY]
[WEATHER]
[TRAVEL_DOMAIN: good_weather]

## Good Weather Rules

[CONDITION]
good_weather

[RULES]

- Prioritize outdoor parks, zoos, beaches, viewpoints, riverside walks, and open public spaces.
- Allow more walking-oriented itineraries.
- Increase flexibility for outdoor sightseeing.

[ITINERARY_BEHAVIOR]

- Use parks and outdoor public areas as major itinerary anchors.
- Combine outdoor attractions within nearby districts.

---

[RULE_CATEGORY]
[WEATHER]
[TRAVEL_DOMAIN: backup_planning]

## Indoor Backup Rules

[CONDITION]
outdoor_heavy_itinerary

[RULES]

- Always provide indoor backup options when the itinerary depends heavily on outdoor activities.
- Keep nearby indoor alternatives available during unstable weather.
- Avoid rigid outdoor-only schedules.

[ITINERARY_BEHAVIOR]

- Maintain itinerary flexibility during weather changes.
- Allow dynamic replacement of weather-sensitive activities.

---

[RULE_CATEGORY]
[WEATHER]
[TRAVEL_DOMAIN: family_weather_adaptation]

## Family Weather Rules

[CONDITION]
family_trip + bad_weather

[RULES]

- Reduce long outdoor walking segments for families with children.
- Increase indoor snack and recovery opportunities.
- Avoid excessive queue-heavy outdoor attractions.
- Prefer compact indoor activities during unstable weather.

[ITINERARY_BEHAVIOR]

- Prioritize comfort and flexibility over attraction quantity.
- Use indoor attractions as pacing stabilizers.