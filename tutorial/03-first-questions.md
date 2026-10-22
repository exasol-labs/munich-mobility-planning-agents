# 3 · First questions

**Goal:** get to know the data together with your agent before it builds anything.

Enter the following prompts in your agent. They describe what you want to see; the agent works out how.

## 3.1 What's in the data

```text
What data do we have about Munich here? Give me an overview: what each group of tables describes, how current it is, and what it can't tell us.
```

## 3.2 Public transport per district

```text
How much public transport does each district get on a typical weekday? A bus and an S-Bahn train carry very different numbers of people, so take that into account.
```

Watch how the agent works: it shows the SQL, runs it, checks the result for plausibility, then answers. It should count capacity rather than departures and name the weekday it uses, Wednesday 21 Oct 2026.

Follow up in your own words, for example:

```text
Why does Altstadt-Lehel get so much? Which modes does it come from?
```

## 3.3 A question the data can't answer

```text
Which district has the worst traffic right now?
```

There is no live traffic, delay or passenger data. The agent says so and offers what the data can show instead.

## 3.4 The research

The [research/](../research/README.md) folder holds the background for the later chapters: population growth per district, the city's plans and the planned rail and tram projects.

```text
Which districts are expected to grow most by 2045, and why? Use the research in this repo.
```


Next: [4 · v1: How well is each district served today, per resident?](04-v1-residents.md)
