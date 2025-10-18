# data-handler.ipynb

- The algorithm uses spaCy’s medium model (en_core_web_md), which balances speed and semantic performance for this use case.
- The “clever engineering” part:

  - Cleans noisy tokens like dates, times, IDs.
  - Operates on phrases/sentences rather than raw strings.
  - Compares incidents and solutions separately.

- The 90% threshold is enforced on average phrase similarity, with max-pooling per phrase (each phrase in A takes its best match in B, then averaged).
- Caching significantly reduces runtime for larger sheets.

**Try it out**

You can run cell 3 (imports), 5 (load data), 7 (preprocessing functions), 9 (dedup function), and 11 (run process) if needed. To inspect the output, open `processed-data/consolidated_incidents.csv` in Excel or pandas.
