package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	mcp "github.com/metoro-io/mcp-golang"
)

type EmotionArgs struct {
	Text string `json:"text"`
}

func handleEmotionDetection(args EmotionArgs) (*mcp.ToolResponse, error) {
	client := &http.Client{Timeout: 30 * time.Second}

	payload, _ := json.Marshal(map[string]string{"text": args.Text})

	url := os.Getenv("EMOTION_SERVICE_URL")
	if url == "" {
		url = "http://localhost:5001/predict"
	}
	resp, err := client.Post(url, "application/json", bytes.NewBuffer(payload))
	if err != nil {
		return nil, fmt.Errorf("request error: %w", err)
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("emotion api error: %s - %s", resp.Status, string(b))
	}
	var out map[string]any
	if err := json.Unmarshal(b, &out); err != nil {
		return nil, fmt.Errorf("decode error: %w", err)
	}
	prediction, _ := out["prediction"].(string)
	emoji, _ := out["emoji"].(string)
	conf, _ := out["confidence"].(float64)
	msg := fmt.Sprintf("Emotion: %s %s (Confidence: %.2f%%)", prediction, emoji, conf*100)
	log.Printf("emotion_detection: %s", msg)
	return mcp.NewToolResponse(mcp.NewTextContent(msg)), nil
}
