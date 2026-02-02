from huggingface_hub import HfApi

SPACE_ID = "Xeroxat/career_conversation"  # your Space ID
api = HfApi()

secrets = api.list_space_secrets(repo_id=SPACE_ID)
print("Secrets in Space:", [s["name"] for s in secrets])
