#!/usr/bin/env python3
"""
Lab 2: LLM Comparison Script
複数のLLMを比較するスクリプト
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

# 環境変数を読み込み
load_dotenv(override=True)

def print_separator(title=""):
    """区切り線を表示"""
    print("\n" + "="*60)
    if title:
        print(f" {title}")
        print("="*60)

def check_api_keys():
    """APIキーの存在を確認"""
    print_separator("API Key Check")
    
    openai_api_key = os.getenv('OPENAI_API_KEY')
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    google_api_key = os.getenv('GOOGLE_API_KEY')
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    groq_api_key = os.getenv('GROQ_API_KEY')

    if openai_api_key:
        print(f"✅ OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("❌ OpenAI API Key not set")
        
    if anthropic_api_key:
        print(f"✅ Anthropic API Key exists and begins {anthropic_api_key[:7]}")
    else:
        print("⚠️  Anthropic API Key not set (optional)")

    if google_api_key:
        print(f"✅ Google API Key exists and begins {google_api_key[:2]}")
    else:
        print("⚠️  Google API Key not set (optional)")

    if deepseek_api_key:
        print(f"✅ DeepSeek API Key exists and begins {deepseek_api_key[:3]}")
    else:
        print("⚠️  DeepSeek API Key not set (optional)")

    if groq_api_key:
        print(f"✅ Groq API Key exists and begins {groq_api_key[:4]}")
    else:
        print("⚠️  Groq API Key not set (optional)")

def generate_question():
    """LLMに質問するための問題を生成"""
    print_separator("Generating Question")
    
    request = "Please come up with a challenging, nuanced question that I can ask a number of LLMs to evaluate their intelligence. "
    request += "Answer only with the question, no explanation."
    messages = [{"role": "user", "content": request}]
    
    try:
        openai = OpenAI()
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )
        question = response.choices[0].message.content
        print(f"Generated question: {question}")
        return question
    except Exception as e:
        print(f"Error generating question: {e}")
        return "What are the ethical implications of artificial intelligence in healthcare decision-making?"

def get_llm_responses(question):
    """複数のLLMから回答を取得"""
    print_separator("Getting LLM Responses")
    
    competitors = []
    answers = []
    messages = [{"role": "user", "content": question}]
    
    # OpenAI GPT-4o-mini
    try:
        print("🤖 Querying OpenAI GPT-4o-mini...")
        openai = OpenAI()
        response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
        answer = response.choices[0].message.content
        competitors.append("gpt-4o-mini")
        answers.append(answer)
        print("✅ OpenAI response received")
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
    
    # Anthropic Claude
    try:
        print("🤖 Querying Anthropic Claude...")
        claude = Anthropic()
        response = claude.messages.create(
            model="claude-3-5-sonnet-20241022", 
            messages=messages, 
            max_tokens=1000
        )
        answer = response.content[0].text
        competitors.append("claude-3-5-sonnet")
        answers.append(answer)
        print("✅ Anthropic response received")
    except Exception as e:
        print(f"❌ Anthropic error: {e}")
    
    # Google Gemini (if API key available)
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        try:
            print("🤖 Querying Google Gemini...")
            gemini = OpenAI(api_key=google_api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            response = gemini.chat.completions.create(model="gemini-2.0-flash", messages=messages)
            answer = response.choices[0].message.content
            competitors.append("gemini-2.0-flash")
            answers.append(answer)
            print("✅ Google response received")
        except Exception as e:
            print(f"❌ Google error: {e}")
    
    # DeepSeek (if API key available)
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_api_key:
        try:
            print("🤖 Querying DeepSeek...")
            deepseek = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")
            response = deepseek.chat.completions.create(model="deepseek-chat", messages=messages)
            answer = response.choices[0].message.content
            competitors.append("deepseek-chat")
            answers.append(answer)
            print("✅ DeepSeek response received")
        except Exception as e:
            print(f"❌ DeepSeek error: {e}")
    
    # Groq (if API key available)
    groq_api_key = os.getenv('GROQ_API_KEY')
    if groq_api_key:
        try:
            print("🤖 Querying Groq...")
            groq = OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
            response = groq.chat.completions.create(model="llama-3.3-70b-versatile", messages=messages)
            answer = response.choices[0].message.content
            competitors.append("llama-3.3-70b-versatile")
            answers.append(answer)
            print("✅ Groq response received")
        except Exception as e:
            print(f"❌ Groq error: {e}")
    
    return competitors, answers

def display_responses(competitors, answers):
    """回答を表示"""
    print_separator("LLM Responses")
    
    for i, (competitor, answer) in enumerate(zip(competitors, answers), 1):
        print(f"\n--- Response {i}: {competitor} ---")
        print(answer)
        print("-" * 50)

def judge_responses(question, competitors, answers):
    """回答を評価・ランキング"""
    print_separator("Judging Responses")
    
    together = ""
    for index, answer in enumerate(answers):
        together += f"# Response from competitor {index+1}\n\n"
        together += answer + "\n\n"
    
    judge_prompt = f"""You are judging a competition between {len(competitors)} competitors.
Each model has been given this question:

{question}

Your job is to evaluate each response for clarity and strength of argument, and rank them in order of best to worst.
Respond with JSON, and only JSON, with the following format:
{{"results": ["best competitor number", "second best competitor number", "third best competitor number", ...]}}

Here are the responses from each competitor:

{together}

Now respond with the JSON with the ranked order of the competitors, nothing else. Do not include markdown formatting or code blocks."""
    
    try:
        openai = OpenAI()
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": judge_prompt}],
        )
        results = response.choices[0].message.content
        print("Judgment results:")
        print(results)
        
        # JSONをパースしてランキングを表示
        try:
            results_dict = json.loads(results)
            ranks = results_dict["results"]
            print_separator("Final Rankings")
            for index, result in enumerate(ranks):
                competitor = competitors[int(result)-1]
                print(f"Rank {index+1}: {competitor}")
        except json.JSONDecodeError:
            print("Could not parse JSON results")
            
    except Exception as e:
        print(f"Error in judging: {e}")

def main():
    """メイン関数"""
    print_separator("Lab 2: LLM Comparison")
    print("複数のLLMを比較するスクリプトを開始します...")
    
    # APIキーをチェック
    check_api_keys()
    
    # 質問を生成
    question = generate_question()
    
    # LLMから回答を取得
    competitors, answers = get_llm_responses(question)
    
    if not competitors:
        print("❌ 利用可能なLLMがありません。APIキーを確認してください。")
        return
    
    # 回答を表示
    display_responses(competitors, answers)
    
    # 回答を評価
    judge_responses(question, competitors, answers)
    
    print_separator("Complete")
    print("スクリプトが完了しました！")

if __name__ == "__main__":
    main()


