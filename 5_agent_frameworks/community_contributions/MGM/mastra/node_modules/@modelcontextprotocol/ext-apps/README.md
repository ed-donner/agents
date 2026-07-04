<!-- LOGO -->
<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="media/mcp-white.svg">
    <source media="(prefers-color-scheme: light)" srcset="media/mcp.svg">
    <img src="media/mcp.svg" alt="MCP Apps" width="128">
  </picture>
  <h1>MCP Apps</h1>
  <p>
    Build interactive UIs for MCP tools — charts, forms, dashboards — that render inline in Claude, ChatGPT and any other compliant chat client.
    <br /><br />
    <a href="#why-mcp-apps">Why</a>
    ·
    <a href="https://apps.extensions.modelcontextprotocol.io/api/documents/Quickstart.html">Quickstart</a>
    ·
    <a href="https://apps.extensions.modelcontextprotocol.io/api/">API Docs</a>
    ·
    <a href="https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx">Spec</a>
    ·
    <a href="CONTRIBUTING.md">Contributing</a>
  </p>
</div>

<p align="center">
  <a href="https://github.com/modelcontextprotocol/ext-apps/actions/workflows/ci.yml"><img src="https://github.com/modelcontextprotocol/ext-apps/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="License: Apache 2.0"></a>
  <a href="https://www.npmjs.com/package/@modelcontextprotocol/ext-apps"><img src="https://img.shields.io/npm/v/@modelcontextprotocol/ext-apps.svg" alt="npm version"></a>
  <a href="https://www.npmjs.com/package/@modelcontextprotocol/ext-apps"><img src="https://img.shields.io/npm/dm/@modelcontextprotocol/ext-apps.svg" alt="npm downloads"></a>
  <a href="https://github.com/modelcontextprotocol/ext-apps"><img src="https://img.shields.io/github/stars/modelcontextprotocol/ext-apps" alt="GitHub stars"></a>
  <a href="https://apps.extensions.modelcontextprotocol.io/api/"><img src="https://img.shields.io/badge/docs-API%20Reference-blue" alt="API Documentation"></a>
</p>

<p align="center">
  <img src="media/excalidraw.gif" alt="MCP Apps demo" width="600">
  <br><em>Excalidraw built with MCP Apps, running in Claude</em>
</p>

## Table of Contents

- [Build with Agent Skills](#build-with-agent-skills)
- [Supported Clients](#supported-clients)
- [Why MCP Apps?](#why-mcp-apps)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Using the SDK](#using-the-sdk)
- [Examples](#examples)
- [Specification](#specification)
- [Resources](#resources)
- [Contributing](#contributing)

## Build with Agent Skills

The fastest way to build an MCP App is to let your AI coding agent do it. This
repo ships four [Agent Skills](https://agentskills.io/) — install them once,
then just ask:

| Skill                                                                       | What it does                                                | Try it                                |
| --------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------- |
| [`create-mcp-app`](./plugins/mcp-apps/skills/create-mcp-app/SKILL.md)       | Scaffolds a new MCP App with an interactive UI from scratch | _"Create an MCP App"_                 |
| [`migrate-oai-app`](./plugins/mcp-apps/skills/migrate-oai-app/SKILL.md)     | Converts an existing OpenAI App to use MCP Apps             | _"Migrate from OpenAI Apps SDK"_      |
| [`add-app-to-server`](./plugins/mcp-apps/skills/add-app-to-server/SKILL.md) | Adds interactive UI to an existing MCP server's tools       | _"Add UI to my MCP server"_           |
| [`convert-web-app`](./plugins/mcp-apps/skills/convert-web-app/SKILL.md)     | Turns an existing web app into a hybrid web + MCP App       | _"Add MCP App support to my web app"_ |

### Install the Skills

**Claude Code** — install via the plugin marketplace:

```
/plugin marketplace add modelcontextprotocol/ext-apps
/plugin install mcp-apps@modelcontextprotocol-ext-apps
```

**Other agents** — any AI coding agent that supports
[Agent Skills](https://agentskills.io/) can use these skills. See the
[agent skills guide](./docs/agent-skills.md) for manual installation
instructions.

Once installed, verify by asking your agent _"What skills do you have?"_ — you
should see `create-mcp-app`, `migrate-oai-app`, `add-app-to-server`, and
`convert-web-app` in the list. Then just ask it to create or migrate an app and
it will guide you through the rest.

## Supported Clients

<p align="center">
  <a href="https://developers.openai.com/apps-sdk/mcp-apps-in-chatgpt/"><img src="https://img.shields.io/badge/ChatGPT-docs-74aa9c?logo=openai&logoColor=white" alt="ChatGPT"></a>
  <a href="https://claude.com/docs/connectors/building/mcp-apps/getting-started"><img src="https://img.shields.io/badge/Claude-docs-d97706?logo=claude&logoColor=white" alt="Claude"></a>
  <a href="https://code.visualstudio.com/blogs/2026/01/26/mcp-apps-support"><img src="https://img.shields.io/badge/VS_Code-docs-007ACC?logo=visualstudiocode&logoColor=white" alt="VS Code"></a>
  <a href="https://block.github.io/goose/docs/tutorials/building-mcp-apps/"><img src="https://img.shields.io/badge/Goose-docs-000000?logo=goose&logoColor=white" alt="Goose"></a>
  <a href="https://learning.postman.com/docs/postman-ai/mcp-requests/interact"><img src="https://img.shields.io/badge/Postman-docs-FF6C37?logo=postman&logoColor=white" alt="Postman"></a>
  <a href="https://www.mcpjam.com/blog/mcp-apps-example"><img src="https://img.shields.io/badge/MCPJam-docs-8B5CF6" alt="MCPJam"></a>
</p>

> [!NOTE]
> MCP Apps is an extension to the
> [core MCP specification](https://modelcontextprotocol.io/specification). Host
> support varies — see the
> [clients page](https://modelcontextprotocol.io/clients) for the full list.

## Why MCP Apps?

MCP tools return text and structured data. That works for many cases, but not
when you need an interactive UI, like a chart, form, design canvas or video player.

MCP Apps provide a standardized way to deliver interactive UIs from MCP servers.
Your UI renders inline in the conversation, in context, in any compliant host.

## How It Works

MCP Apps extend the Model Context Protocol by letting tools declare UI
resources:

1. **Tool definition** — Your tool declares a `ui://` resource containing its
   HTML interface
2. **Tool call** — The LLM calls the tool on your server
3. **Host renders** — The host fetches the resource and displays it in a
   sandboxed iframe
4. **Bidirectional communication** — The host passes tool data to the UI via
   notifications, and the UI can call other tools through the host

## Getting Started

```bash
npm install -S @modelcontextprotocol/ext-apps
```

**New here?** Start with the
[Quickstart Guide](https://apps.extensions.modelcontextprotocol.io/api/documents/Quickstart.html)
to build your first MCP App.

## Using the SDK

The SDK serves three roles: app developers building interactive Views, host
developers embedding those Views, and MCP server authors registering tools with
UI metadata.

| Package                                     | Purpose                                                   | Docs                                                                                                                |
| ------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `@modelcontextprotocol/ext-apps`            | Build interactive Views (App class, PostMessageTransport) | [API Docs →](https://apps.extensions.modelcontextprotocol.io/api/modules/app.html)                                  |
| `@modelcontextprotocol/ext-apps/react`      | React hooks for Views (useApp, useHostStyles, etc.)       | [API Docs →](https://apps.extensions.modelcontextprotocol.io/api/modules/_modelcontextprotocol_ext-apps_react.html) |
| `@modelcontextprotocol/ext-apps/app-bridge` | Embed and communicate with Views in your chat client      | [API Docs →](https://apps.extensions.modelcontextprotocol.io/api/modules/app-bridge.html)                           |
| `@modelcontextprotocol/ext-apps/server`     | Register tools and resources on your MCP server           | [API Docs →](https://apps.extensions.modelcontextprotocol.io/api/modules/server.html)                               |

There's no _supported_ host implementation in this repo (beyond the
[examples/basic-host](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-host)
example).

The [MCP-UI](https://github.com/idosal/mcp-ui) client SDK offers a
fully-featured MCP Apps framework used by a few hosts. Clients may choose to use
it or roll their own implementation.

## Examples

The
[`examples/`](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples)
directory contains demo apps showcasing real-world use cases.

<!-- prettier-ignore-start -->
| | | |
|:---:|:---:|:---:|
| [![Map](examples/map-server/grid-cell.png "Interactive 3D globe viewer using CesiumJS")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/map-server) | [![Three.js](examples/threejs-server/grid-cell.png "Interactive 3D scene renderer")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/threejs-server) | [![ShaderToy](examples/shadertoy-server/grid-cell.png "Real-time GLSL shader renderer")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/shadertoy-server) |
| [**Map**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/map-server) | [**Three.js**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/threejs-server) | [**ShaderToy**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/shadertoy-server) |
| [![Sheet Music](examples/sheet-music-server/grid-cell.png "ABC notation to sheet music")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/sheet-music-server) | [![Wiki Explorer](examples/wiki-explorer-server/grid-cell.png "Wikipedia link graph visualization")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/wiki-explorer-server) | [![Cohort Heatmap](examples/cohort-heatmap-server/grid-cell.png "Customer retention heatmap")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/cohort-heatmap-server) |
| [**Sheet Music**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/sheet-music-server) | [**Wiki Explorer**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/wiki-explorer-server) | [**Cohort Heatmap**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/cohort-heatmap-server) |
| [![Scenario Modeler](examples/scenario-modeler-server/grid-cell.png "SaaS business projections")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/scenario-modeler-server) | [![Budget Allocator](examples/budget-allocator-server/grid-cell.png "Interactive budget allocation")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/budget-allocator-server) | [![Customer Segmentation](examples/customer-segmentation-server/grid-cell.png "Scatter chart with clustering")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/customer-segmentation-server) |
| [**Scenario Modeler**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/scenario-modeler-server) | [**Budget Allocator**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/budget-allocator-server) | [**Customer Segmentation**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/customer-segmentation-server) |
| [![System Monitor](examples/system-monitor-server/grid-cell.png "Real-time OS metrics")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/system-monitor-server) | [![Transcript](examples/transcript-server/grid-cell.png "Live speech transcription")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/transcript-server) | [![Video Resource](examples/video-resource-server/grid-cell.png "Binary video via MCP resources")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/video-resource-server) |
| [**System Monitor**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/system-monitor-server) | [**Transcript**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/transcript-server) | [**Video Resource**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/video-resource-server) |
| [![PDF Server](examples/pdf-server/grid-cell.png "Interactive PDF viewer with chunked loading")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/pdf-server) | [![QR Code](examples/qr-server/grid-cell.png "QR code generator")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/qr-server) | [![Say Demo](examples/say-server/grid-cell.png "Text-to-speech demo")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/say-server) |
| [**PDF Server**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/pdf-server) | [**QR Code (Python)**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/qr-server) | [**Say Demo**](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/say-server) |

### Starter Templates

| | |
|:---:|:---|
| [![Basic](examples/basic-server-react/grid-cell.png "Starter template")](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-react) | The same app built with different frameworks — pick your favorite!<br><br>[React](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-react) · [Vue](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-vue) · [Svelte](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-svelte) · [Preact](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-preact) · [Solid](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-solid) · [Vanilla JS](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-server-vanillajs) |
<!-- prettier-ignore-end -->

### Running the Examples

#### With basic-host

To run all examples locally using
[basic-host](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples/basic-host)
(the reference host implementation included in this repo):

```bash
git clone https://github.com/modelcontextprotocol/ext-apps.git
cd ext-apps
npm install
npm start
```

Then open http://localhost:8080/.

#### With MCP Clients

Every Node.js example is published as `@modelcontextprotocol/server-<name>`. To
add one to an MCP client that supports stdio (Claude Desktop, VS Code, etc.),
use this pattern:

```json
{
  "mcpServers": {
    "<name>": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-<name>", "--stdio"]
    }
  }
}
```

For example, to add the map server: `@modelcontextprotocol/server-map`. The
Python examples (`qr-server`, `say-server`) use `uv run` instead — see their
READMEs for details.

#### Local Development

To test local modifications with an MCP client, clone the repo, install, then
point your client at a local build:

```json
{
  "mcpServers": {
    "<name>": {
      "command": "bash",
      "args": [
        "-c",
        "cd ~/code/ext-apps/examples/<name>-server && npm run build >&2 && node dist/index.js --stdio"
      ]
    }
  }
}
```

## Specification

<div align="center">

| Version        | Status      | Link                                                                                                                              |
| -------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **2026-01-26** | Stable      | [specification/2026-01-26/apps.mdx](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx) |
| **draft**      | Development | [specification/draft/apps.mdx](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/draft/apps.mdx)           |

</div>

## Resources

- [Quickstart Guide](https://apps.extensions.modelcontextprotocol.io/api/documents/Quickstart.html)
- [API Documentation](https://apps.extensions.modelcontextprotocol.io/api/)
- [Specification (2026-01-26)](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx)
  ([Draft](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/draft/apps.mdx))
- [SEP-1865 Discussion](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/1865)

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines on how to get started, submit pull requests, and report issues.
