# Azure Container Apps Dynamic Sessions Setup

This guide explains how to set up secure, isolated Python code execution using Azure Container Apps Dynamic Sessions for the LangGraph agent.

## Prerequisites

1. **Azure CLI**
   ```bash
   brew install azure-cli  # macOS
   ```

2. **Azure Account** 

[Create free account with $250 credit](https://azure.microsoft.com/free/)
And setup Azure subscription

3. **Login to Azure**
   ```bash
   az login
   ```

4. **Setup MFAA for the user**
Startiung 10/2025 Azure requires MFA for all accounts. Make sure to set it up

## Quick Setup

### Run the Setup Script

```bash
cd 4_langgraph/community_contributions/dkisselev-zz

./setup_azure_sessions.sh \
  --resource-group "your-resource-group" \
  --location "eastus"
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--resource-group` | **Yes** | - | Azure resource group name |
| `--location` | No | `eastus` | Azure region |
| `--session-pool-name` | No | `python-session-pool` | Session pool name |
| `--environment-name` | No | `session-env` | Container environment name |
| `--max-sessions` | No | `10` | Maximum concurrent sessions |
| `--cooldown-period` | No | `300` | Cooldown in seconds |

### What the Script Does

1. Verifies Azure CLI and login
2. Registers required resource providers
3. Creates resource group
4. Creates Container Apps environment
5. Creates Python session pool
6. Assigns permissions
7. Updates `.env` file with endpoint

## Testing

After setup, test the integration:

```bash
cd 4_langgraph/community_contributions/dkisselev-zz
uv run python app.py
```

**Test prompt:** `Calculate 89 to the power of 47 using Python`

Expected: A 92-digit number starting with `6427752177...`

This proves Python is executing in Azure (LLMs can't compute this accurately).

## Cost Management

Azure Container Apps costs depend on:
- Number of sessions
- Session duration  
- Resource allocation

**Tips:**
- Use appropriate `--max-sessions` for your needs
- Set `--cooldown-period` to control session lifecycle
- Monitor usage in Azure Portal
- Set up budget alerts

## Cleanup

Remove all resources when done:

```bash
# Delete entire resource group
az group delete --name "your-resource-group" --yes --no-wait

# Or delete just the session pool
az containerapp sessionpool delete \
  --name "python-session-pool" \
  --resource-group "your-resource-group" \
  --yes
```

## Additional Resources

- [Azure Container Apps Dynamic Sessions](https://learn.microsoft.com/azure/container-apps/sessions)
- [LangChain Azure Sessions](https://python.langchain.com/docs/integrations/tools/azure_dynamic_sessions)
- [Azure CLI Reference](https://learn.microsoft.com/cli/azure/)

