from huggingface_hub import HfApi
from dotenv import dotenv_values

SPACE_ID = "Xeroxat/intellapersona"

# Load .env from parent directory
env_vars = dotenv_values("../.env")

if not env_vars:
    print("⚠️ Warning: No variables found in .env file!")
    exit()

print(f"Found {len(env_vars)} variables in .env file")

api = HfApi()

# Upload each variable as a Space secret
success_count = 0
for key, value in env_vars.items():
    try:
        api.add_space_secret(repo_id=SPACE_ID, key=key, value=value)
        print(f"✅ Added secret: {key}")
        success_count += 1
    except Exception as e:
        print(f"❌ Failed to add {key}: {str(e)}")

print(f"\n{success_count}/{len(env_vars)} secrets uploaded successfully!")

