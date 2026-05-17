# Seasonality Rules

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: summer_planning]

## Summer Travel Rules

[CONDITION]
season = summer

[RULES]

- Avoid long outdoor walks during the hottest midday hours.
- Prioritize outdoor activities during morning and evening periods.
- Include shaded parks, riverside walks, beaches, and outdoor cafes.
- Add hydration and recovery breaks during high temperatures.
- Reduce dense sightseeing blocks during heat waves.

[ITINERARY_BEHAVIOR]

- Schedule museums and indoor attractions during midday.
- Use outdoor activities primarily during cooler hours.
- Prefer flexible pacing during extreme heat.

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: winter_planning]

## Winter Travel Rules

[CONDITION]
season = winter

[RULES]

- Reduce outdoor exposure time during cold weather.
- Prioritize museums, aquariums, indoor attractions, and warm cafes.
- Avoid long outdoor waiting periods.
- Use shorter walking routes during severe cold or wind.

[ITINERARY_BEHAVIOR]

- Add more indoor recovery opportunities.
- Prefer compact district-based itineraries during cold weather.

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: family_travel]

## Family Winter Rules

[CONDITION]
season = winter + family_trip + child_under_6

[RULES]

- Reduce outdoor walking duration for families with small children.
- Prioritize indoor attractions and warm rest areas.
- Avoid excessive transportation-heavy schedules during cold weather.

[ITINERARY_BEHAVIOR]

- Use cafes, indoor museums, and aquariums as pacing stabilizers.
- Reduce attraction density during cold conditions.

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: spring_autumn_planning]

## Spring and Autumn Rules

[CONDITION]
season = spring OR season = autumn

[RULES]

- Use mixed indoor and outdoor itineraries.
- Prioritize walking routes, parks, architecture, and moderate sightseeing density.
- Use flexible pacing to adapt to unstable weather conditions.

[ITINERARY_BEHAVIOR]

- Combine parks and museums within the same itinerary day.
- Use moderate pacing with weather-aware backup options.

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: rainy_weather]

## Rainy Season Rules

[CONDITION]
rainy_weather

[RULES]

- Always include indoor backup activities.
- Reduce exposed outdoor walking routes.
- Avoid weather-sensitive viewpoints and long outdoor queues.
- Prioritize museums, aquariums, indoor cafes, and covered attractions.

[ITINERARY_BEHAVIOR]

- Replace weather-sensitive attractions with indoor alternatives.
- Increase itinerary flexibility during unstable weather.

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: tourism_density]

## Peak Tourist Season Rules

[CONDITION]
peak_tourist_season

[RULES]

- Avoid scheduling too many crowded attractions in one day.
- Reduce dense sightseeing in peak midday tourist periods.
- Prefer less crowded districts during high tourism periods.

[ITINERARY_BEHAVIOR]

- Add recovery and flexible time blocks during crowded travel periods.
- Reduce transportation-heavy schedules during peak tourism.

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: weather_instability]

## Unstable Weather Rules

[CONDITION]
unstable_weather

[RULES]

- Prefer itineraries with nearby indoor alternatives.
- Avoid tightly packed outdoor-only schedules.
- Use flexible pacing during changing weather conditions.

[ITINERARY_BEHAVIOR]

- Keep backup indoor attractions available throughout the itinerary.
- Increase itinerary adaptability and reduce rigid scheduling.

---

[RULE_CATEGORY]
[SEASONALITY]
[TRAVEL_DOMAIN: extreme_heat]

## Extreme Heat Rules

[CONDITION]
extreme_heat

[RULES]

- Avoid intensive uphill walking during midday.
- Prioritize shaded parks, indoor museums, beaches, and cafes.
- Increase hydration and recovery opportunities.
- Reduce activity density during the hottest hours.

[ITINERARY_BEHAVIOR]

- Schedule sightseeing earlier in the day.
- Use indoor attractions as midday anchors.