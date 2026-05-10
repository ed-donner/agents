# Setup GitHubToolkit
https://reference.langchain.com/python/langchain-community/agent_toolkits/github/toolkit/GitHubToolkit

```sh
pip install -U pygithub
export GITHUB_APP_ID="your-app-id"
export GITHUB_APP_PRIVATE_KEY="path-to-private-key"
export GITHUB_REPOSITORY="your-github-repository"
```

---
## Install pygithub
`uv add pygithub` - it will add to the existing packages changing uv.lock and project.toml files
---

## How to Create a GitHub App for Langchain GitHubToolkit (for Private Repos)

1. **Go to GitHub Developer Settings**
   - Visit: https://github.com/settings/apps
   - Click **"New GitHub App"**.

2. **Fill Out GitHub App Details**
   - **App name:** Choose a unique name (e.g., “Langchain Toolkit App”).
   - **Homepage URL:** You can use your project’s homepage or your repo URL (e.g., https://github.com/mihaly-hazag/test-repo).
   - **Description:** (Optional) e.g., “App for Langchain GitHubToolkit integration.”
   - **User or Organization:** Choose your user or organization account.
   - **Webhook URL:** Leave blank unless you need webhooks.
   - **Webhook secret:** Leave blank unless you need webhooks.

3. **Set Permissions**
   - Under **Repository permissions**, set the following (minimum for read access):
     - **Contents:** Read-only (or Read & write if you need to push)
     - **Metadata:** Read-only
     - **Pull requests:** Read-only (or Read & write if you need to create PRs)
     - **Issues:** Read-only (or Read & write if you need to create issues)
   - Add other permissions as needed for your use case.

4. **Subscribe to Events (Optional)**
   - If you want to receive webhook events, select the events you need (optional for Langchain).

5. **Where Can This GitHub App Be Installed?**
   - Choose “Any account” (default).

6. **Create the App**
   - Click **"Create GitHub App"** at the bottom.

7. **Generate and Download the Private Key**
   - After creation, scroll down to **"Private keys"**.
   - Click **"Generate a private key"**.
   - Download the `.pem` file. This is your **GITHUB_APP_PRIVATE_KEY** (the file path or its contents).

8. **Get the App ID**
   - On the app’s page, you’ll see **App ID** (a number). This is your **GITHUB_APP_ID**.

9. **Install the App on Your Private Repository**
   - On the app’s page, click **"Install App"** (right sidebar).
   - Choose your account/organization.
   - Select the private repository (or all repositories) you want the app to access.
   - Complete the installation.

10. **Set Up Environment Variables**
   - In your `.env` file:
     - `GITHUB_APP_ID="your-app-id"` (replace with the number from step 8)
     - `GITHUB_APP_PRIVATE_KEY="path-to-private-key"` (or paste the contents, but keep formatting)

11. **(Optional) Get Installation ID**
   - Some APIs require the installation ID. You can find it in the URL after installing the app, or via the GitHub API.

### Security Tips
- Never share your private key.
- Store the `.pem` file securely.
- Do not commit your `.env` file or private key to version control.

---

