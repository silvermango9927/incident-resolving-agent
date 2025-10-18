# chache-requests.py

From anywhere in your code import the function and call it with the incident string.
Example:

```from
cause = get_root_cause_for_incident("Database connection failed for order #12345 at 10:30 AM")
print(cause) # String or None
```

It defaults to en_core_web_md, and falls back to en_core_web_sm if the medium model isn't available.
The default CSV path is resolved relative to cache-requests.py at data/processed-data/consolidated_incidents.csv.

The lookup compares cleaned-to-cleaned text and uses phrase-level averaging with max pooling, same as the notebook `data-handler.ipynb`.
If you edit the CSV, the dataset cache will refresh because its keyed by file modification time.
