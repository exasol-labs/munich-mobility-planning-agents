# 9 · A new series: cycling coverage

**Goal:** `munich-cycling-coverage`: the planning question asked for bikes. How much cycle network does each district have, compared with the city average? This dashboard is v1 of a new series; the exercises at the end are yours to build.

## The idea

The city's cycle network data has about 21,000 segments, each with a length and a path type. Not every meter is worth the same: a separated cycle track serves cyclists better than a painted lane or a sidewalk where cycling is allowed. So the network is weighted by quality. The weights are an assumption, and the viewer should be able to change them. A starting point:

| Path type | Weight |
|---|---|
| Cycle track (Radweg), cycle street (Fahrradstraße) | 1.0 |
| Separated cycle and footpath | 0.8 |
| Painted lane (Radfahr-/Schutzstreifen) | 0.6 |
| Shared footpath (Gemeinsamer Geh- und Radweg) | 0.5 |
| Sidewalk, cycling allowed | 0.3 |

There are two ways to compare districts, and they tell different stories:
- **Per person:** network per resident and job, so growth without new paths lowers a district's value over time.
- **Per km²:** network density by area, which doesn't change with the year.

The city also runs six permanent bicycle counters. They measure use, but only at six points (five of them with data).

## The prompt

```text
Start a new series with a dashboard munich-cycling-coverage, titled "Munich Cycling Coverage", in the same look as the planning dashboards.

I want to see how well each district is served for cycling: how much cycle network it has, weighted by path quality, compared with the city average. Let me switch between per person (residents and jobs, with the year slider and job weight as before) and per km². Let me change the quality weights per path type, with a way to reset them. Leave out segments that aren't usable paths, such as connectors, and count two-way paths for both directions.

Show the bicycle counters on the map with their average bikes per day and how much rain reduces them. Below the map, show what each district's network is made of by path quality.

Show me the per-person and per-km² rankings before you build the page.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/munich-cycling-coverage

- Per person, which districts are thin? Now switch to per km². What happens to the same districts?
- Move the year to 2045 in the per-person view. Which district falls furthest, and why?
- Set the weight of the shared footpaths to 0. Which districts drop?
- Hover over the counters. Which one counts the most bikes, and how much does rain reduce it?

## What the data can't tell you

- **Supply only:** network length and path type. Nothing on width, surface, continuity, gaps, junction safety or motor traffic.
- **Measured use at five points,** January to July 2026. One counter can't stand for a whole district.
- **The weights are assumptions,** not an official quality scale.
- **The 2045 view assumes no new paths.** The dataset contains no planned cycling projects.

## Exercises: continue the series

Each exercise is a new version. Describe what you want to see, as in the earlier chapters, and let your agent build it.

1. **Change since 2024.** As in v3 of the planning series: how much does each district's cycle network per person change as the city grows?
2. **Cycling projects as scenarios.** As in v4: [research/plans-facts.md](../research/plans-facts.md) lists the city's cycling projects (section 3). Ask your agent which of them have enough detail (street, district, length, year) to model, and switch them on and off.
3. **Roadworks on cycle paths.** Which cycle paths are affected by current roadworks, and how much high-quality network does each district lose while they last?
4. **An assistant,** as in v5, with a context pack built from [research/cycling-coverage.md](../research/cycling-coverage.md) and the data model.
5. **Bike-share history.** The Munich open data portal has the historical MVG Rad bike-share trips (the service ended in September 2025). `scripts/prepare_dataset.py --with-mvg-bikes` adds them to the dataset when you rebuild it from the portal download (see [Rebuilding the CSVs yourself](../data/README.md#rebuilding-the-csvs-yourself-optional)). Where did trips start and end, and how does that relate to the network?

Stuck? See [10 · Troubleshooting](10-troubleshooting.md).
