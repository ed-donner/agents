package main

import (
	"encoding/json"
	"log"

	mcp "github.com/metoro-io/mcp-golang"
	mcpstdio "github.com/metoro-io/mcp-golang/transport/stdio"
)

type ToolsListParams struct{}

type InitializeParams struct{}

func main() {
	transport := mcpstdio.NewStdioServerTransport()
	server := mcp.NewServer(transport)

	// tools/list
	_ = server.RegisterTool("tools/list", "List available tools", func(_ ToolsListParams) (*mcp.ToolResponse, error) {
		resp := map[string]any{
			"tools": []map[string]any{
				{
					"name":        "initialize",
					"description": "Initialize MCP server",
					"parameters": map[string]any{
						"type":       "object",
						"properties": map[string]any{},
					},
				},
				{
					"name":        "tools/list",
					"description": "List available tools",
					"parameters": map[string]any{
						"type":       "object",
						"properties": map[string]any{},
					},
				},
				{
					"name":        "emotion_detection",
					"description": "Analyze text to detect emotions using AI",
					"parameters": map[string]any{
						"type":     "object",
						"required": []string{"text"},
						"properties": map[string]any{
							"text": map[string]any{"type": "string", "description": "The text to analyze for emotion"},
						},
					},
				},
			},
		}
		b, _ := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": nil, "result": resp})
		return mcp.NewToolResponse(mcp.NewTextContent(string(b))), nil
	})

	// emotion_detection
	_ = server.RegisterTool("emotion_detection", "Analyze text to detect emotions using AI", handleEmotionDetection)

	// initialize
	_ = server.RegisterTool("initialize", "Initialize MCP server", func(_ InitializeParams) (*mcp.ToolResponse, error) {
		cap := map[string]any{
			"tools":     map[string]any{"listChanged": true},
			"resources": map[string]any{"listChanged": false},
			"prompts":   map[string]any{"listChanged": false},
		}
		info := map[string]any{"name": "Emotion Detection MCP Server", "version": "1.0.0"}
		res := map[string]any{"capabilities": cap, "serverInfo": info}
		b, _ := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": nil, "result": res})
		return mcp.NewToolResponse(mcp.NewTextContent(string(b))), nil
	})

	if err := server.Serve(); err != nil {
		log.Fatalf("failed to serve: %v", err)
	}
	select {}
}
