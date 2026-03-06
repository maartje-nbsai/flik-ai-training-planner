# Workshop Assignment: AI-Powered Training Planner for Ultimate Frisbee

## Context

Flik Ultimate (flikulti.com) is a platform with hundreds of training materials for Ultimate Frisbee coaches and players — covering tactics, drills, practice sessions, video tutorials, and strength & conditioning.

**Your team:**
- **Maartje** is the trainer and your point of contact. She can give you access to the Flik platform as a team member, so you can explore all the available content. Follow this link to be added to the team and get access: https://www.flikulti.com/team?code=092dfa1e14db869049a251e7

- **The prep work is done:** Maartje has already scraped, cleaned, and loaded all Flik training materials into a vector store. You don't need to build that part. See `TECHNICAL_DETAILS.md` for how to access and query it.

---

## The Problem

Flik has an enormous library of content — but as a trainer, finding the right material for a specific training session takes too much time and effort. You need to browse categories manually, cross-reference drills with theory, and figure out a logical progression yourself. This gets in the way of actually coaching.

---

## What We Want

A tool where a trainer can describe what they want to train — in their own words — and get back a concrete, ready-to-use training plan. Fast, with minimal effort.

The trainer should be able to:

1. **Describe their intent** — for example:
   - *"I want to work on breaking the mark with my intermediate club team"*
   - *"My players struggle with timing their cuts in a vertical stack"*
   - *"We're playing a team that runs cup zone next weekend, how do we prepare?"*

2. **Receive a concrete training plan** — not just a list of links, but a structured plan they can walk onto the pitch with, including:
   - A clear theme or objective for the session
   - Relevant drills or exercises
   - Supporting theory or context where useful
   - Links back to the source material on flikulti.com

3. **Get a short-term progression** — not just one session, but a suggestion for the next 2–3 sessions in case the topic requires multiple steps, repetition, or a build-up.

---

## The AI Challenge

You are building an AI-powered assistant on top of the vector store. There are three parts to this challenge:

### 1. RAG: Find the most relevant material
Use the vector store (see `TECHNICAL_DETAILS.md`) to retrieve the Flik content that is most relevant to what the trainer describes. Think about:
- What makes a good search query to send to the vector store?
- How many results do you retrieve, and how do you filter or rank them?
- How do you handle cases where the results aren't great?

### 2. Interface: Make it easy to get good input
The quality of the output depends heavily on what the trainer tells the system. Design an interface that naturally collects the right information without feeling like filling in a form. Think about:
- What does the trainer actually need to tell the system? (e.g. skill level, team size, session length, focus area)
- How do you get this from them with minimal friction?
- Could a short conversation (a few follow-up questions) improve the result?

### 3. LLM logic: Turn documents into a training plan
Once you have relevant content from the vector store, you need to use an LLM to turn it into a coherent, useful output. Think about:
- How do you structure the prompt so the LLM produces a practical training plan, not just a summary?
- How do you handle progression across multiple sessions?
- How do you make sure the output stays grounded in the actual Flik material (with links), rather than making things up?

---

## What a Good Result Looks Like

A trainer types something like:

> *"I want to work on handler resets with my club team. They understand the basics but execute poorly under pressure. We have 90 minutes."*

And they get back something like:

> **Session 1 – Handler Resets: Building Confidence Under Pressure**
> *Goal: Improve reset timing and decision-making when marked aggressively*
>
> **Warm-up (15 min):** ...
> **Main drill (30 min):** 45-degree dump drill — [flikulti.com/drills/45-degree-dump](https://www.flikulti.com/drills/45-degree-dump)
> **Themed game (30 min):** ...
> **Cool-down & debrief (15 min):** ...
>
> **Session 2 – Adding Pressure**
> ...
>
> **Session 3 – Live Application**
> ...

---

## Deliverables

By the end of the workshop, you should have a working prototype that:

- Takes a trainer's description as input
- Retrieves relevant content from the Flik vector store
- Produces a structured training plan using an LLM
- Presents the output in a way a trainer can actually use on the pitch

The interface can be as simple as a command-line prompt or as polished as a small web UI — what matters is that the end-to-end flow works and the output is genuinely useful.

---

## Bonus: Give It Back to the Community

Flik Ultimate is a non-profit, and its mission is to support the growth of Ultimate Frisbee worldwide. If this tool works, it shouldn't stay in a prototype — it should live on their website and be available to every coach who visits.

As a bonus challenge, think about how to hand this off in a way that the Flik team can actually use and maintain, without needing a team of developers.

### What this means in practice

- **Make it embeddable** — can your solution be dropped into an existing website as a simple widget or page? A lightweight web app (e.g. a single HTML page, or a small backend with a clean API) is much easier to adopt than a complex standalone system.
- **Keep dependencies minimal** — the Flik team are coaches and content creators, not engineers. The fewer moving parts, the better. If your solution requires managing a server, a database, and three API keys to keep running, it's unlikely to survive long-term.
- **Document what's needed to run it** — what API keys are required? What does it cost to run per month? What happens when the Flik content is updated — how does the vector store get refreshed?
- **Think about access** — the full Flik content library is behind a subscription. The tool on the website should work for logged-in members. How does your solution handle that?

### Why this matters

There are thousands of Ultimate Frisbee coaches around the world — club coaches, national team coaches, volunteers running youth programmes — who would benefit from a tool like this. A well-built prototype that can realistically be deployed is a meaningful contribution to a sport that runs almost entirely on volunteer effort.

You don't have to fully solve this in the workshop. But if your design choices make integration easier — clean API, no hardcoded secrets, a UI that could sit inside a WordPress page — that's a win worth aiming for.

---

## Getting Started

1. Read `TECHNICAL_DETAILS.md` — this explains how to query the vector store
2. Get access to flikulti.com — ask Maartje to add you as a team member
3. Browse a few pages on the site to understand the content and structure
4. Start with the RAG layer: can you retrieve relevant content for a sample trainer input?
5. Then add the LLM layer: can you turn that content into a training plan?
