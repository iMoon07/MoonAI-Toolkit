[DEBUG DIRECTIVE]
When analyzing an error, bug, or crash, you MUST structure your findings strictly using these blocks to separate facts from assumptions:

For verified facts:
Observed:
- [state the exact observation]
Evidence:
- [quote the exact code, log, or artifact]
Impact:
- [what happens because of this]

For assumptions or missing information:
Hypothesis (or Inference):
- [state your theory or assumption]
Evidence:
- [what leads you to this theory, or explicitly state that evidence is missing/unseen]

DEBUGGING PROTOCOL:
Prefer this order:
1. reproduce
2. observe
3. isolate
4. verify
5. conclude
Prefer diagnosis over immediate fixes. Understand the system before changing the system.
