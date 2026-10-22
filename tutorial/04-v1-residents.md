# 4 · v1: How well is each district served today, per resident?

**Goal:** the first dashboard, `munich-mobility-planning-v1`: a map of Munich's 25 districts that shows at a glance which ones get less public transport per resident than the city average.

## The idea

In chapter 3 you saw that a raw count of departures treats a bus like an S-Bahn train. The measure for this series is **places offered**: each scheduled trip counts with the number of people it can carry. Dividing by residents and comparing with the city as a whole gives one number per district:

- 1.0× means the district gets as many places per resident as Munich on average.
- 0.5× means half as many, 2× twice as many.

A planner looks at the districts well below 1.0×, especially the dense ones, where many people share the service.

## The prompt

```text
Build my first dashboard, munich-mobility-planning-v1, titled "Munich Mobility Planning".

I want a map of the 25 districts that shows how well each one is served by public transport today, per resident: the places offered on a typical weekday per resident, relative to the Munich average. It should be obvious at a glance which districts are below and which are above average, and very high or very low values shouldn't wash out the rest of the map. Mark the densest districts, because a gap there affects more people. When I hover over a district, show me the numbers behind its color.

Before you build anything, show me the SQL and the result per district, and tell me which districts come out lowest and highest.
```

The agent shows the query and the ranking first. That is the moment to ask questions, for example "why is Sendling-Westpark so low?", or to change the approach before the page exists.

## Look at it

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v1

- Which districts are clearly below average? Are any of the dense ones among them?
- Hover over Altstadt-Lehel. How far above average is it, and what does the color show?
- Open "SQL executed" at the bottom. Can you follow how the number for one district is computed?

Change what you don't like, in your own words:
```text
The labels overlap in the city center. Make the map easier to read there.
```

## Understand it

```text
Explain in plain words how the color of a district is computed, step by step. Which of these steps are assumptions, and how would the map change if we made them differently?
```

## What the data can't tell you

- The data is the **scheduled** timetable: no passengers, crowding, delays or live traffic.
- Capacities are planning values per mode or line, not measured loads.
- A ratio per district says nothing about walking distance. A district can look well served because rail lines run through it.

Next: [5 · v2: residents and jobs](05-v2-jobs.md)
