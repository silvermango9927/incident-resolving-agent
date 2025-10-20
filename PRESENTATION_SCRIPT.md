Title: Mavericks – Incident Resolving Agent (4‑minute walkthrough)

1. Problem and Goals (0:00–0:30)

- Duty officers are flooded with incident reports. We need fast, grounded decisions:
  detect duplicates, identify root causes, suggest actions, and communicate clearly.
- Design principles: modular multi‑agent system, well‑curated tools, and grounded retrieval from a knowledge base.

2. Architecture Overview (0:30–1:10)

- Three agents orchestrated end‑to‑end:
  - Cause Analysis Agent: caching (duplicate detection), knowledge‑base search, GCRNN‑style cause development, and ranking.
  - Remediation Agent: turns problem descriptions into an ordered course of action using a supervised baseline with an RL‑ready harness.
  - Execution Agent: determines the right contact, drafts an email, and compiles the escalation summary.
- Decision Maker/Orchestrator coordinates tools and enforces consent before actions.

3. Caching System and Vector DB (1:10–1:40)

- We convert the consolidated CSV into a persistent Chroma vector DB. Why Chroma? It’s local‑first, lightweight, and fast for cosine search.
- Embeddings use sentence-transformers all-MiniLM-L6-v2 to stay lightweight yet strong for semantic similarity.
- Duplicate detection now uses ANN lookups rather than full spaCy similarity, reducing latency and increasing robustness.

4. Knowledge Base and Grounding (1:40–2:05)

- PDFs are chunked and embedded into a separate “kb_docs” collection. Retrieval provides evidence for cause ranking.
- We also support extracting relationships from incident data so the graph‑based cause model can learn component–fault structure later.

5. Cause Development (2:05–2:30)

- We scaffold a GCRNN/graph model path to map incidents to a subgraph and score candidate causes. In this iteration it’s a placeholder with a clean API so you can drop in the trained network.
- Ranking fuses signals from cache match, KB retrieval, and model scores to produce an ordered list of likely causes.

6. Remediation Strategy (2:30–3:00)

- Baseline: a simple supervised classifier over an “action catalog” to map problems to actionable steps.
- RL‑ready: a PPO harness stub is provided to evolve the policy later using incident outcomes as rewards.

7. Execution Agent and Summary (3:00–3:30)

- Contacts are selected semantically from a processed CSV (product team escalation list). Email drafting uses Jinja templates and supports an optional local LLM polish later (ollama/llama.cpp).
- SMTP credentials are read from env vars; without them, the system defaults to safe dry‑run mode.
- The Escalation Summary is emitted as structured JSON and Markdown/HTML following the slide format.

8. Why this design works (3:30–4:00)

- Speed: ANN vector search and lightweight models keep the loop responsive.
- Grounding: KB retrieval, explicit metadata, and consistent schemas improve reliability.
- Modularity: Each agent/tool is swappable; e.g., upgrade the GCRNN or plug a new vector DB without touching orchestration.
- Safety and control: consent gates and dry‑run email ensure no unintended actions.

Close with: “You now have a complete, extensible code base that mirrors the slide design and is production‑ready to iterate: swap in a trained GCRNN, turn on PPO fine‑tuning, and connect real SMTP when you’re ready.”
