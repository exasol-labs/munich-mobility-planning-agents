# 5 · v2: Residents and jobs

**Goal:** `munich-mobility-planning-v2`: the v1 map, counting the people who work in a district as well as those who live there. You need v1 from [chapter 4](04-v1-residents.md).

## The idea

In v1 the old town looks six times better served than the city. But Altstadt-Lehel has few residents and many offices, shops and universities: much of its capacity carries people who work there. A fairer picture counts both:

> activity = residents + w × jobs

How much a job weighs against a resident is a judgment, so w becomes a control. At w = 0 the map is v1; at w = 1 a job counts as much as a resident.

The jobs per district are the city's modeled estimate of workers at their place of work. Munich publishes no open per-district employment count.

## The prompt

```text
Now build v2 as munich-mobility-planning-v2, starting from v1.

Residents aren't the whole demand: people also travel to the districts where they work. Count jobs too, with a weight I can set, from 0 (residents only, as in v1) to 1.5, default 1. The comparison with the city average should use the same weight. "Dense" should then mean dense in residents and jobs. In the hover, also show the jobs, and flag districts that are both dense and among the least served.

Before you build it, show me how the ranking changes between weight 0 and weight 1.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v2

- What happens to Altstadt-Lehel and the city center at w = 1?
- Which districts stay low, whatever the weight? Those are the robust findings.
- Set w to 0. Is it exactly v1 again?
- Which districts get outlined as dense once jobs count?

## Understand it

```text
Which districts move most when I change the job weight, and why? What would be a sensible weight to argue for, and what does the choice depend on?
```

## What the data can't tell you

- Jobs are a modeled estimate (base year 2022), rounded to 100, not a count.
- Nothing here says how many residents or workers use public transport, or when they travel.
- w = 1 doesn't mean "a worker makes as many trips as a resident". It is a weighting you choose.

Next: [6 · v3: the forecast to 2045](06-v3-forecast.md)
