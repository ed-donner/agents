# Extra setup details for NodeJS and Playwright

_In Cursor, right click on this file in the Explorer and select "Open Preview" to see it with formatting, or look at the version online in Github._

In weeks 4 and 6, we will make use of NodeJS on your computer.

PC users take note: if you are using WSL (which you will need to in Week 6), then at that point you will need to install node again on your Ubuntu side.

## Instructions for installing Node

Check if you have node installed - should be v22 or later:  
`!node --version` 

Here are super clear installation instructions, courtesy of our AI friend:

https://chatgpt.com/share/68103af2-e2dc-8012-b259-bc135a23273b

In most cases, this involves simply visiting https://nodejs.org and follow the instructions. PC users on WSL, remember to follow the Linux instructions.

When complete, check that this works in the notebook. You may need to quit and relaunch Cursor (also close any open terminals in Cursor).

`!node --version`  
`!npx --version`

## Installing Playwright

Playwright is the browser automation software from Microsoft that we use in weeks 4 and 6.

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