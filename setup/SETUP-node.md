# Extra setup details for NodeJS and Playwright

_In Cursor, right click on this file in the Explorer and select "Open Preview" to see it with formatting, or look at the version online in Github._

In weeks 4 and 6, we will make use of NodeJS on your computer.

PC users take note: if you are using WSL (which you will need to in Week 6), then at that point you will need to install node again on your Ubuntu side.

## Instructions for installing Node

Check if you have node installed - should be v22 or later:  
`!node --version` 

If you need to install it, use your platform's package manager - one command, no decisions to make:

On Windows, in PowerShell:  
`winget install OpenJS.NodeJS.LTS`

On Mac, in Terminal:  
`brew install node`

On Linux (and PC users on WSL, which you will need in Week 6), follow the Linux instructions at https://nodejs.org/en/download - or if the package managers above aren't available to you (for example a locked-down work machine), go to that same page, ignore the Docker and version-manager options, and use the **Windows Installer (.msi)** / **macOS Installer (.pkg)** button with all the defaults.

**After installing, quit Cursor completely and start it again** (and close any open terminals). A freshly installed Node is invisible to programs that were already running, and restarting just the notebook kernel is not enough - the kernel inherits its environment from Cursor. After the restart, check that this works in the notebook:

`!node --version`  
`!npx --version`

## Installing Playwright

Playwright is the browser automation software from Microsoft that we use in weeks 4 and 6.

**Week 4 (refreshed labs): there is nothing to install.** The lab runs Playwright's MCP server with `npx`, which fetches it on demand, and it drives the copy of Google Chrome already on your machine (Chrome needs to be installed, but not running). The Week 4 Day 3 lab includes a check cell that proves the whole chain before you use it. If that cell reports Chrome is not found, install Chrome normally or run `npx playwright install chrome` in a terminal.

**Week 6 only**, where the labs use the Python playwright package, you also need its managed browsers:

On Mac / PC:  
`uv run playwright install`

On Linux / WSL:  
`uv run playwright install --with-deps chromium`

## Troubleshooting - if node-based MCP servers hang on Windows / WSL

For some WSL users, running npx based MCP servers seems to hang. Here is the fix!

First, quit and relaunch Cursor, to pick up any changes since you installed node. Also, exit any open Terminals in Cursor and open a new terminal.

In the terminal, run:  
`which node`

This should give you a path to node running on your WSL subsystem. Suppose it's something like:  
`/home/user/.nvm/versions/node/v22.18.0/bin`

Then run this command, carefully replacing the path here with your one:   
`!export PATH="/home/user/.nvm/versions/node/v22.18.0/bin:$PATH"`  

Also this, again carefully replacing the path with your one:  
`os.environ["PATH"] = "/home/user/.nvm/versions/node/v22.18.0/bin:" + os.environ["PATH"]`

And then try the prior cell again.  
And if even that doesn't work, try changing the MCP params with the full path of npx:

```python
playwright_params = {"command": "/home/user/.nvm/versions/node/v22.18.0/bin/npx","args": [ "@playwright/mcp@latest"]}
```

And / or this approach:

```python
env = {"PATH": "/home/user/.nvm/versions/node/v22.18.0/bin:" + os.environ["PATH"]}
playwright_params = {"command": "npx","args": [ "@playwright/mcp@latest"], "env": env}
```

If that doesn't work, let me know! A heartfelt thank you to Radoslav R. and André R. for battling with this, finding the fixes and sharing them!