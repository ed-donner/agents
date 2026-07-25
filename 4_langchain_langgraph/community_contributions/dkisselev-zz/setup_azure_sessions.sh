#!/bin/bash

# This script automates the setup of Azure Container Apps for secure Python code execution
# Compatible with macOS and Linux

set -e  # Exit on error

# Default values
LOCATION="eastus"
SESSION_POOL_NAME="python-session-pool"
ENVIRONMENT_NAME="session-env"
MAX_SESSIONS=10
COOLDOWN_PERIOD=300
RESOURCE_GROUP=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Show usage
usage() {
    cat << EOF
Usage: $0 --resource-group <name> [options]

Required:
  --resource-group <name>       Azure resource group name

Optional:
  --location <region>           Azure region (default: eastus)
  --session-pool-name <name>    Session pool name (default: python-session-pool)
  --environment-name <name>     Container Apps environment name (default: session-env)
  --max-sessions <number>       Maximum concurrent sessions (default: 10)
  --cooldown-period <seconds>   Cooldown period in seconds (default: 300)
  --help                        Show this help message

Example:
  $0 --resource-group my-rg --location westus2 --max-sessions 20

EOF
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --resource-group)
            RESOURCE_GROUP="$2"
            shift 2
            ;;
        --location)
            LOCATION="$2"
            shift 2
            ;;
        --session-pool-name)
            SESSION_POOL_NAME="$2"
            shift 2
            ;;
        --environment-name)
            ENVIRONMENT_NAME="$2"
            shift 2
            ;;
        --max-sessions)
            MAX_SESSIONS="$2"
            shift 2
            ;;
        --cooldown-period)
            COOLDOWN_PERIOD="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate required parameters
if [ -z "$RESOURCE_GROUP" ]; then
    print_error "Resource group name is required"
    usage
fi

print_info "Starting Azure Container setup..."
echo ""
print_info "Configuration:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Location: $LOCATION"
echo "  Session Pool Name: $SESSION_POOL_NAME"
echo "  Environment Name: $ENVIRONMENT_NAME"
echo "  Max Sessions: $MAX_SESSIONS"
echo "  Cooldown Period: ${COOLDOWN_PERIOD}s"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed"
    echo "Install: brew install azure-cli (macOS)"
    exit 1
fi

print_info "Azure CLI found: $(az --version | head -n1)"

# Configure Azure CLI to avoid interactive prompts
print_info "Configuring Azure CLI..."
az config set extension.use_dynamic_install=yes_without_prompt &> /dev/null || true
az config set extension.dynamic_install_allow_preview=true &> /dev/null || true

# Install containerapp extension if needed
if ! az extension show --name containerapp &> /dev/null; then
    print_info "Installing containerapp extension..."
    az extension add --name containerapp --yes &> /dev/null || \
        az extension add --name containerapp --upgrade --yes
    print_info "Extension installed"
else
    print_info "Extension already available"
fi
echo ""

# Verify Azure login
print_info "Verifying Azure login..."
if ! az account show &> /dev/null; then
    print_error "Not logged into Azure. Please run: az login"
    exit 1
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_info "Using subscription: $SUBSCRIPTION_ID"
echo ""

# Register Azure resource provider
print_info "Registering Azure resource provider"
for provider in "Microsoft.App" "Microsoft.OperationalInsights"; do
    STATE=$(az provider show -n $provider --query "registrationState" -o tsv 2>/dev/null || echo "NotRegistered")
    if [ "$STATE" != "Registered" ]; then
        print_info "Registering $provider..."
        az provider register -n $provider --wait
    fi
done
print_info "Resource providers ready"
echo ""

# Step 1: Create or verify resource group
print_info "Step 1/5: Checking resource group..."
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_info "Resource group exists"
else
    print_info "Creating resource group..."
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --output none
    print_info "Resource group created"
fi
echo ""

# Step 2: Create Container Apps environment
print_info "Step 2/5: Checking Container Apps environment..."
if az containerapp env show --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_info "Environment exists"
else
    print_info "Creating Container Apps environment"
    echo ""
    az containerapp env create \
        --name "$ENVIRONMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" || {
            echo ""
            print_error "Failed to create environment"
            exit 1
        }
    echo ""
    print_info "Environment created"
fi
echo ""

# Step 3: Create session pool
print_info "Step 3/5: Checking session pool..."
if az containerapp sessionpool show --name "$SESSION_POOL_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_info "Session pool exists"
else
    # Get environment location
    ENV_LOCATION=$(az containerapp env show \
        --name "$ENVIRONMENT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query "location" \
        -o tsv 2>/dev/null)
    POOL_LOCATION="${ENV_LOCATION:-$LOCATION}"
    
    print_info "Creating session pool (background deployment)..."
    
    # Create session pool asynchronously
    az containerapp sessionpool create \
        --name "$SESSION_POOL_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$POOL_LOCATION" \
        --container-type PythonLTS \
        --max-sessions "$MAX_SESSIONS" \
        --cooldown-period "$COOLDOWN_PERIOD" \
        --no-wait || {
            print_error "Failed to initiate session pool creation"
            exit 1
        }
    
    print_info "Waiting for session pool (timeout: 10 minutes)..."
    
    # Poll for completion
    TIMEOUT=600
    ELAPSED=0
    INTERVAL=15
    
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if az containerapp sessionpool show --name "$SESSION_POOL_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
            STATUS=$(az containerapp sessionpool show \
                --name "$SESSION_POOL_NAME" \
                --resource-group "$RESOURCE_GROUP" \
                --query "properties.provisioningState" \
                -o tsv 2>/dev/null)
            
            if [ "$STATUS" = "Succeeded" ]; then
                echo ""
                print_info "Session pool ready"
                break
            elif [ "$STATUS" = "Failed" ]; then
                echo ""
                print_error "Session pool creation failed. Check Azure Portal"
                exit 1
            fi
        fi
        echo -n "."
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done
    
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo ""
        print_warning "Timed out waiting for session pool"
        print_warning "Creation is still running. Check Azure Portal or wait and continue."
    fi
fi
echo ""

# Step 4: Retrieve pool management endpoint
print_info "Step 4/5: Retrieving pool endpoint..."
POOL_ENDPOINT=$(az containerapp sessionpool show \
    --name "$SESSION_POOL_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query "properties.poolManagementEndpoint" \
    --output tsv)

if [ -z "$POOL_ENDPOINT" ]; then
    print_error "Failed to retrieve endpoint"
    exit 1
fi

print_info "Endpoint: ${POOL_ENDPOINT:0:50}..."
echo ""

# Step 5: Assign permissions
print_info "Step 5/5: Assigning permissions..."
USER_OBJECT_ID=$(az ad signed-in-user show --query id -o tsv 2>/dev/null)

if [ -z "$USER_OBJECT_ID" ]; then
    print_warning "Could not get user ID. Skipping role assignment."
    print_warning "Azure CLI credentials should still work via DefaultAzureCredential."
else
    SCOPE="/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/sessionPools/$SESSION_POOL_NAME"
    
    if az role assignment list --assignee "$USER_OBJECT_ID" --scope "$SCOPE" --query "[?roleDefinitionName=='Container Apps SessionPools Contributor']" -o tsv 2>/dev/null | grep -q .; then
        print_info "Role already assigned"
    else
        if az role assignment create \
            --role "Container Apps SessionPools Contributor" \
            --assignee "$USER_OBJECT_ID" \
            --scope "$SCOPE" \
            --output none 2>&1; then
            print_info "Role assigned"
        else
            print_warning "Role assignment failed (may need admin permissions)"
            print_warning "Azure CLI credentials should still work."
        fi
    fi
fi
echo ""

# Update .env file
print_info "Updating .env file..."
ENV_FILE="$(dirname "$0")/.env"
[ ! -f "$ENV_FILE" ] && ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    if grep -q "^AZURE_CONTAINER_ENDPOINT=" "$ENV_FILE"; then
        # Update existing
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^AZURE_CONTAINER_ENDPOINT=.*|AZURE_CONTAINER_ENDPOINT=${POOL_ENDPOINT}|" "$ENV_FILE"
        else
            sed -i "s|^AZURE_CONTAINER_ENDPOINT=.*|AZURE_CONTAINER_ENDPOINT=${POOL_ENDPOINT}|" "$ENV_FILE"
        fi
        print_info ".env updated"
    else
        # Add new
        echo "" >> "$ENV_FILE"
        echo "# Azure Container Apps Dynamic Sessions" >> "$ENV_FILE"
        echo "AZURE_CONTAINER_ENDPOINT=${POOL_ENDPOINT}" >> "$ENV_FILE"
        print_info ".env updated"
    fi
else
    print_warning ".env file not found. Please add manually:"
    echo "  AZURE_CONTAINER_ENDPOINT=${POOL_ENDPOINT}"
fi
echo ""

# Summary
print_info "=========================================="
print_info "Setup Complete!"
print_info "=========================================="
echo ""
echo "Resources:"
echo "  Resource Group:  $RESOURCE_GROUP"
echo "  Location:        $LOCATION"
echo "  Session Pool:    $SESSION_POOL_NAME"
echo "  Environment:     $ENVIRONMENT_NAME"
echo ""
print_info "Done!"

