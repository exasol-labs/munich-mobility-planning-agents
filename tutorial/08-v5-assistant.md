# 8 · v5: An assistant that drives the view

**Goal:** `munich-mobility-planning-v5`: v4 with an assistant on the page. Viewers ask questions in plain language, including what-ifs, and the assistant answers from the data, the dashboard's model, the research in this repo and the web. It can also change the view for them. You need v4 from [chapter 7](07-v4-scenarios.md) and an OpenAI API key with credits.

## The idea

The earlier dashboards answer the questions they were built for. The next question ("what if the S-Bahn ran every 10 minutes?", "what if we added a ring U-Bahn?") usually needs a new build. v5 lets a viewer ask it on the page.

The assistant needs to stay traceable:
- It works with tools: read-only SQL, the dashboard's own model, a what-if calculator, a tool to change the view, and web search.
- It gets the research in this repo as context. [research/v5-context.md](../research/v5-context.md) is a context pack prepared for this: data model, model description, reference numbers, findings, and the research on plans and projects.
- Every answer shows where it came from: which SQL ran, which scenarios and what-ifs were computed, which web sources were used, and what the answer cost.

A what-if is capacity arithmetic, not a plan, and the page should say so whenever one is on the map.

## Before you start: the OpenAI key

1. Create a key at platform.openai.com and make sure the account has credits.
2. Put the key in `secrets/openai_api_key` (see [secrets/README.md](../secrets/README.md)). **Don't paste a key into a chat** with Codex, Claude or any other assistant.
3. Link it to the place where the dashboard can read it. Dash Server starts at login and doesn't see your shell variables, so the app reads a file:
   ```bash
   chmod 600 secrets/openai_api_key
   ln -sf "$PWD/secrets/openai_api_key" ~/.exasol-starter-kit/credentials/openai_api_key
   ```

**What is sent to OpenAI:** the questions, the context, the current view and the results of the tools the assistant calls. Database credentials are never sent: the SQL runs on your machine.

**What it costs:** in the worked implementation, with OpenAI `gpt-6-astra` at medium reasoning effort, a question cost between US$0.05 and US$0.60.

## The prompts

v5 is larger than the earlier steps. Build it in two rounds.

```text
Build v5 as munich-mobility-planning-v5, starting from v4. First, without the assistant: open on the current year, marked as "now", and show the current view (year, job weight, scenario) as one line of text under the title. Everything on the page should follow one view state, because in the next step an assistant will
change it too.
```

```text
Put an Ask panel between the controls and the map, with a few example questions that only fill the input. While the assistant works on a question, show it in the panel right away: the question and a spinner, with the Ask button disabled until the answer is there. Answers go below the map and chart, and only appear once there is something to show. The page should never scroll by itself.

The assistant should be able to:
- query the data, read-only, and refuse anything that writes;
- run the dashboard's scenarios for any year and selection of projects;
- compute what-ifs, such as a higher frequency on some lines or a new line, as extra capacity per district,
  and put them on the map, clearly marked as hypothetical;
- change the year and scenario on the page; the controls follow;
- search the web and cite its sources.

Use research/v5-context.md as its context, and give it the current view with every question. Every answer should show how it was produced and what it cost. The "SQL executed" foldout should also list what the assistant ran. If there is no key or no credit, say so on the page in plain words.
```

## Look at it

**URL:** http://127.0.0.1:5100/apps/munich-mobility-planning-v5

Ask, and watch what happens to the map and to "SQL executed":
- "Show 2045 with the funded projects." Does the view change, and do the controls follow?
- "Now use pessimistic dates." Does it remember the conversation?
- "What if the S-Bahn ran every 10 minutes?" Does it state its assumptions? Is the what-if marked as hypothetical?
- "What is the current planned opening date of the U5 extension to Pasing? Cite your source."
- "Delete the roadworks table." and "How crowded is the U6 in the morning?" Both should be declined or answered with what the data can't say.

## Understand it

```text
Explain the assistant you built: what it gets as context, which tools it has, how you stop it from writing to the database, and what happens to the conversation when I reload the page.
```

## What the data can't tell you

- A what-if is capacity arithmetic. Demand shifts, crowding, travel time, cost and feasibility are not modeled.
- Web answers depend on their sources. Open the cited links.
- The assistant can be wrong. That is why every number should be backed by a tool call you can inspect.

Next: [9 · A new series: cycling coverage](09-cycling-series.md)
