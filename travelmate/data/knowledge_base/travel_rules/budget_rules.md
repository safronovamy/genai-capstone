# Budget Planning Rules

---

[RULE_CATEGORY]
[BUDGET]
[TRAVEL_DOMAIN: itinerary_planning]

## Low Budget Rules

[CONDITION]
budget = low

[RULES]

- Prioritize free attractions, parks, public viewpoints, playgrounds, beaches, and walking routes.
- Prefer low-cost museums and short indoor visits.
- Reduce the number of premium paid attractions.
- Avoid scheduling multiple expensive activities on the same day.
- Prefer districts with multiple nearby free attractions.
- Use public transportation and walkable routes when possible.

[ITINERARY_BEHAVIOR]

- Prefer outdoor and public-space activities during good weather.
- Use museums selectively during bad weather.
- Avoid premium tours and luxury dining recommendations unless explicitly requested.

---

[RULE_CATEGORY]
[BUDGET]
[TRAVEL_DOMAIN: itinerary_planning]

## Medium Budget Rules

[CONDITION]
budget = medium

[RULES]

- Allow a balanced mix of free and paid attractions.
- Include museums, zoos, aquariums, and occasional premium experiences.
- Balance indoor and outdoor activities depending on weather conditions.
- Combine paid attractions with lower-cost walking or park activities.

[ITINERARY_BEHAVIOR]

- Allow 1 major paid attraction per day if relevant.
- Use cafes and restaurants as optional comfort points rather than premium experiences.

---

[RULE_CATEGORY]
[BUDGET]
[TRAVEL_DOMAIN: itinerary_planning]

## High Budget Rules

[CONDITION]
budget = high

[RULES]

- Allow premium attractions, guided tours, and comfort-focused experiences.
- Reduce attraction density to improve comfort and flexibility.
- Include premium dining or high-quality indoor experiences when relevant.
- Prioritize convenience and reduced travel fatigue.

[ITINERARY_BEHAVIOR]

- Allow premium indoor backup options during bad weather.
- Prefer scenic and comfort-oriented experiences over overloaded schedules.

---

[RULE_CATEGORY]
[BUDGET]
[TRAVEL_DOMAIN: conflict_resolution]

## Budget Contradiction Handling

[CONDITION]
luxury_request + low_budget

[RULES]

- Explain the contradiction between requested luxury experiences and the specified budget.
- Suggest lower-cost alternatives when possible.
- Prioritize the most valuable experiences instead of maximizing attraction count.

[RESPONSE_BEHAVIOR]

- The system should communicate trade-offs clearly.
- The system should avoid unrealistic itinerary promises.

---

[RULE_CATEGORY]
[BUDGET]
[TRAVEL_DOMAIN: family_travel]

## Family Budget Rules

[CONDITION]
family_trip + low_budget

[RULES]

- Prioritize playgrounds, parks, beaches, and free outdoor spaces.
- Avoid excessive transportation-heavy schedules.
- Prefer attractions with free or low-cost child-friendly activities.
- Reduce unnecessary attraction density to avoid fatigue-related spending.

[ITINERARY_BEHAVIOR]

- Use parks and public spaces as recovery points between attractions.
- Prefer flexible schedules over expensive tightly packed itineraries.