# Extra setup details for NodeJS and Playwright

_In Cursor, right click on this file in the Explorer and select "Open Preview" to see it with formatting, or look at the version online in Github._

In weeks 4 and 6, we will make use of NodeJS on your computer.

PC users take note: if you choose to use WSL, then you will need to install node again on your Ubuntu side.

## Instructions for installing Node

Check if you have node installed - should be v22 or later:  
`!node --version` 

If you need to install it, use your platform's package manager:

On Windows, in PowerShell:  
`winget install OpenJS.NodeJS.LTS`

On Mac, in Terminal:  
`brew install node`

On Linux (and PC users on WSL), follow the Linux instructions at https://nodejs.org/en/download - or if the package managers above aren't available to you (for example a locked-down work machine), go to that same page, ignore the Docker and version-manager options, and use the **Windows Installer (.msi)** / **macOS Installer (.pkg)** button with all the defaults.

**After installing, quit Cursor completely and start it again** (and close any open terminals). A freshly installed Node is invisible to programs that were already running, and restarting just the notebook kernel is not enough - the kernel inherits its environment from Cursor. After the restart, check that this works in the notebook:

`!node --version`  
`!npx --version`
