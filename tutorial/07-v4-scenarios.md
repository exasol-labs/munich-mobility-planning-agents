# 7 · v4: Rail and tram projects as scenarios

**Goal:** `munich-mobility-planning-v4`: v3 with the planned rail and tram projects as scenarios you can switch on and off, to see how much of the decline to 2045 they make up, and where.
You need v3 from [chapter 6](06-v3-forecast.md).

## The idea

The city and the state are building or planning 17 rail and tram projects: new tram lines, U5 extensions, the 2nd S-Bahn trunk tunnel (2. Stammstrecke) and more. Some are funded and under construction; others are only under discussion. The dataset holds each project's stations, opening year, status and funding, curated from official sources ([research/pt-projects-notes.md](../research/pt-projects-notes.md)).

A project adds capacity at its stations from its opening year on. Two questions need a modeling decision:
- **How much service does a new line get?** Where a frequency is published, use it. Where none is, borrow the service of a comparable existing line.
- **What does the 2nd Stammstrecke change?** The new tunnel adds trains at its own stations. The operating concept also promises at least 15-minute service on most S-Bahn lines. This tutorial assumes nothing is taken away from the existing trunk, and that every S-Bahn line except S2, S5, S7 and S20 runs at least every 15 minutes. Read the notes on the 2nd Stammstrecke in the research before you decide.

Opening years slip. A "pessimistic dates" option uses the published risk years instead.

## The prompt

```text
Build v4 as munich-mobility-planning-v4, starting from v3.

I want to switch the planned rail and tram projects on and off, alone or in groups: none, the funded ones, the funded and planned ones, and everything that has been discussed. A project should count from its opening year, with an option to use the later risk years instead. Show the stations of the active projects on the map, and tell me in one line how many projects are active in the selected year and how much capacity they add.

For the 2nd Stammstrecke: count the new-tunnel trains, remove nothing from the existing trunk, and assume at least 15-minute service on all S-Bahn lines except S2, S5, S7 and S20.

Before you build the page, show me for 2045 how the city and the districts come out with no projects, with the funded projects and with all of them.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v4

- Set 2045 and switch on the funded projects. How much of the decline do they make up? Which districts gain most, and which get nothing?
- Step the slider back and watch the projects open one after another.
- Switch on pessimistic dates. What changes in 2035, and what in 2045?
- Switch on everything. Where does Aubing-Lochhausen-Langwied's recovery come from, and is that project funded?

Ask for changes in your own words, for example:
```text
I want to see each project's funding status and whether its data is verified, next to its name.
```

## Understand it

```text
For the 2nd Stammstrecke, break down where its added capacity comes from: which lines and stations, and how much from the new tunnel versus the 15-minute service. Which of these numbers are the most uncertain?
```

## What the data can't tell you

- Opening years, frequencies and comparable lines are assumptions from public sources. Projects without a published year are placed at 2040.
- The 2nd Stammstrecke line table is unverified, and the 2025 tender may change it.
- The model adds capacity where the stations are. It doesn't know whether people would use it, how travel times change, or whether a project is built on time or at all.

Next: [8 · v5: an assistant that drives the view](08-v5-assistant.md)
