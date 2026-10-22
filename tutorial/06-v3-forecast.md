# 6 · v3: The forecast to 2045, if nothing is added

**Goal:** `munich-mobility-planning-v3`: v2 with a year slider to 2045 and a chart of how each district changes, assuming the timetable stays as it is today. You need v2 from [chapter 5](05-v2-jobs.md).

## The idea

Munich is forecast to grow from 1.60 M residents (2024) to 1.83 M (2045), mostly at the edges of the city. If no service is added, every new resident and job shares the existing capacity. This version shows where that has the largest effect.

Two choices make the years comparable:
- Every year is compared with the **2024** city average.
- The city publishes district forecasts for 2045 (residents) and 2040 (jobs) only, so the years in between are interpolated.

[research/district-growth.md](../research/district-growth.md) has the forecast figures and the large development areas behind them.

## The prompt

```text
Build v3 as munich-mobility-planning-v3, starting from v2.

I want to see what happens as Munich grows to 2045 if public transport stays exactly as it is today. Add a year slider from 2024 to 2045. Residents and jobs should follow the city's forecasts. The map should always compare with today's city average, so I can see districts falling behind as the city grows.

Next to the map, add a chart "Change since 2024": how much each district gains or loses compared with 2024, with Munich overall at the top and then the districts from best to worst.

Tell me how you get residents and jobs for the years in between, and show me the result for 2045 first.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v3

- Move the slider to 2045. Which districts fall furthest? Compare with the development areas in the research.
- How much does the city lose from 2024 to 2026, from growth alone?
- Which districts barely change, and why?

## Understand it

```text
For Aubing-Lochhausen-Langwied, walk me through the numbers in 2024 and 2045: residents, jobs, places and the ratio. How much of the decline comes from residents and how much from jobs?
```

## What the data can't tell you

- The years in between are a straight line between two published points, not a yearly forecast.
- Holding today's timetable is a thought experiment. The timetable changes every year; the 2027 timetable takes effect on 13 Dec 2026 (see [research/plans-facts.md](../research/plans-facts.md)).
- Fewer places per person doesn't mean fuller trains. There is no passenger or crowding data.

Next: [7 · v4: rail and tram projects as scenarios](07-v4-scenarios.md)
