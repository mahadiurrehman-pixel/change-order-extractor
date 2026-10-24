import json

from change_order_extractor.groq_client import extract_change_order

sample = """
Change Order #104 for Riverside Office.
The client requested additional electrical work costing $4,500.
The work will extend the project schedule by 10 days.
Approval is pending.
"""

result = extract_change_order(sample)

print(json.dumps(result.model_dump(), indent=2))