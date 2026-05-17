# Pacing Rules

---

[RULE_CATEGORY]
[PACING]
[TRAVEL_DOMAIN: itinerary_planning]

## Slow Pace Rules

[CONDITION]
pace = slow

[RULES]

- Limit the itinerary to no more than 2 major attractions per day.
- Prefer relaxed walking routes and flexible schedules.
- Include regular rest opportunities between activities.
- Avoid excessive transportation-heavy itineraries.
- Reduce transitions between distant districts.

[ITINERARY_BEHAVIOR]

- Use parks, cafes, and public spaces as recovery points.
- Prioritize comfort and reduced fatigue over attraction quantity.
- Prefer one major morning activity and one lighter afternoon activity.

---

[RULE_CATEGORY]
[PACING]
[TRAVEL_DOMAIN: itinerary_planning]

## Medium Pace Rules

[CONDITION]
pace = medium

[RULES]

- Allow 2-3 activities per day depending on transportation complexity.
- Balance indoor and outdoor activities.
- Combine nearby attractions into the same itinerary block.
- Avoid long consecutive walking segments without breaks.

[ITINERARY_BEHAVIOR]

- Use moderate pacing with flexible recovery opportunities.
- Avoid overloading evenings after long sightseeing days.

---

[RULE_CATEGORY]
[PACING]
[TRAVEL_DOMAIN: itinerary_planning]

## Active Pace Rules

[CONDITION]
pace = active

[RULES]

- Allow 3-4 activities per day when transportation is efficient.
- Combine sightseeing-heavy routes carefully to avoid exhaustion.
- Use efficient district clustering for active itineraries.
- Avoid excessive queues and transportation delays.

[ITINERARY_BEHAVIOR]

- Prioritize attraction density and route optimization.
- Reduce unnecessary downtime between activities.

---

[RULE_CATEGORY]
[PACING]
[TRAVEL_DOMAIN: family_travel]

## Family Pacing Restrictions

[CONDITION]
family_trip + child_under_6

[RULES]

- Active pacing should be reduced for families with young children.
- Avoid more than 2 major attractions per day.
- Add recovery periods after long walks or transportation.
- Reduce queue-heavy or transportation-heavy schedules.

[ITINERARY_BEHAVIOR]

- Prefer flexible schedules over dense sightseeing.
- Use parks, cafes, and playgrounds as pacing stabilizers.

---

[RULE_CATEGORY]
[PACING]
[TRAVEL_DOMAIN: route_optimization]

## Area Clustering Rules

[CONDITION]
multi_district_day

[RULES]

- Avoid placing distant areas in the same half-day block.
- Group nearby attractions together whenever possible.
- Reduce unnecessary cross-city transportation.
- Avoid repeated transitions between districts.

[ITINERARY_BEHAVIOR]

- Organize itineraries around logical geographic clusters.
- Minimize transportation fatigue.

---

[RULE_CATEGORY]
[PACING]
[TRAVEL_DOMAIN: overload_detection]

## Overload Reduction Rules

[CONDITION]
overloaded_itinerary

[RULES]

- Reduce the number of attractions if pacing becomes unrealistic.
- Prioritize high-value attractions over quantity.
- Remove lower-priority activities first.
- Explain itinerary trade-offs clearly to the user.

[ITINERARY_BEHAVIOR]

- Prefer realistic and comfortable itineraries over aggressive sightseeing plans.
- Preserve itinerary flexibility when reducing overload.

---

[RULE_CATEGORY]
[PACING]
[TRAVEL_DOMAIN: weather_adaptation]

## Weather-Aware Pacing Rules

[CONDITION]
rainy_weather OR extreme_heat

[RULES]

- Reduce outdoor walking intensity during bad weather.
- Add more indoor recovery opportunities.
- Shorten exposed outdoor segments during rain or heat.
- Avoid consecutive weather-sensitive activities.

[ITINERARY_BEHAVIOR]

- Increase itinerary flexibility during unstable weather conditions.
- Use museums, cafes, and indoor attractions as pacing stabilizers.