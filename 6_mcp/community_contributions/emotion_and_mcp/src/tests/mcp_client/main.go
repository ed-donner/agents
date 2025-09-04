package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

type rpcReq struct {
	JSONRPC string      `json:"jsonrpc"`
	ID      int         `json:"id"`
	Method  string      `json:"method"`
	Params  interface{} `json:"params"`
}

func postJSON(endpoint string, v interface{}) (string, error) {
	b, _ := json.Marshal(v)
	resp, err := http.Post(endpoint, "application/json", bytes.NewBuffer(b))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	rb, _ := io.ReadAll(resp.Body)
	return string(rb), nil
}

func main() {
	base := os.Getenv("SG_BASE")
	if base == "" {
		base = "http://localhost:8000"
	}
	fmt.Println("Using supergateway base:", base)

	// 1) Open SSE to get sessionId
	sseURL := base + "/sse"
	resp, err := http.Get(sseURL)
	if err != nil {
		fmt.Println("SSE connect error:", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	scanner := bufio.NewScanner(resp.Body)
	var sessionID string
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if !scanner.Scan() {
			time.Sleep(100 * time.Millisecond)
			continue
		}
		line := scanner.Text()
		// Expect lines like: data: /message?sessionId=...
		if strings.HasPrefix(line, "data: ") && strings.Contains(line, "/message?sessionId=") {
			path := strings.TrimPrefix(line, "data: ")
			u, _ := url.Parse(path)
			q := u.Query()
			sessionID = q.Get("sessionId")
			if sessionID == "" {
				// Fallback: manual parse
				parts := strings.Split(path, "sessionId=")
				if len(parts) == 2 {
					sessionID = strings.TrimSpace(parts[1])
				}
			}
			if sessionID != "" {
				fmt.Println("Got sessionId:", sessionID)
				break
			}
		}
	}
	if sessionID == "" {
		fmt.Println("Failed to obtain sessionId from SSE")
		os.Exit(1)
	}

	messageURL := fmt.Sprintf("%s/message?sessionId=%s", base, url.QueryEscape(sessionID))

	// 1b) Keep listening to SSE for responses and print them
	done := make(chan struct{})
	go func() {
		// Continue scanning the same SSE response for JSON payloads
		for scanner.Scan() {
			line := scanner.Text()
			if !strings.HasPrefix(line, "data: ") {
				continue
			}
			payload := strings.TrimPrefix(line, "data: ")
			if !strings.HasPrefix(strings.TrimSpace(payload), "{") {
				continue
			}
			var evt map[string]any
			if err := json.Unmarshal([]byte(payload), &evt); err != nil {
				continue
			}
			// Print any tool result content if present
			if result, ok := evt["result"].(map[string]any); ok {
				if content, ok := result["content"].([]any); ok && len(content) > 0 {
					if first, ok := content[0].(map[string]any); ok {
						if txt, ok := first["text"].(string); ok && txt != "" {
							fmt.Println("tool result ->", txt)
							close(done)
							return
						}
					}
				}
			}
		}
	}()

	// 2) initialize
	initReq := rpcReq{
		JSONRPC: "2.0",
		ID:      1,
		Method:  "initialize",
		Params: map[string]any{
			"protocolVersion": "2024-11-05",
			"capabilities":    map[string]any{},
			"clientInfo":      map[string]any{"name": "mcp-http-client", "version": "0.1.0"},
		},
	}
	if out, err := postJSON(messageURL, initReq); err != nil {
		fmt.Println("initialize error:", err)
	} else {
		fmt.Println("initialize ->", out)
	}

	// 3) tools/list
	listReq := rpcReq{JSONRPC: "2.0", ID: 2, Method: "tools/list", Params: map[string]any{}}
	if out, err := postJSON(messageURL, listReq); err != nil {
		fmt.Println("tools/list error:", err)
	} else {
		fmt.Println("tools/list ->", out)
	}

	// 4) tools/call emotion_detection
	callReq := rpcReq{
		JSONRPC: "2.0",
		ID:      3,
		Method:  "tools/call",
		Params: map[string]any{
			"name": "emotion_detection",
			"arguments": map[string]any{
				"text": "I am so happy today!",
			},
		},
	}
	if out, err := postJSON(messageURL, callReq); err != nil {
		fmt.Println("tools/call error:", err)
	} else {
		fmt.Println("tools/call ->", out)
	}

	// Wait for SSE-delivered tool result or timeout
	select {
	case <-done:
		// received and printed result
	case <-time.After(10 * time.Second):
		fmt.Println("Timed out waiting for tool result over SSE")
	}
}
