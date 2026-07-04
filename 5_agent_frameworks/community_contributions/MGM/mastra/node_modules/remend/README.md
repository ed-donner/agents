# Remend

Self-healing markdown. Intelligently parses and styles incomplete Markdown blocks.

[![npm version](https://img.shields.io/npm/v/remend)](https://www.npmjs.com/package/remend)

## Overview

Remend is a lightweight utility that handles incomplete Markdown syntax during streaming. When AI models stream Markdown token-by-token, you often get partial formatting markers like unclosed `**bold**` or incomplete `[links](`. Remend automatically completes these unterminated blocks so they render correctly in real-time.

Remend powers the markdown termination logic in [Streamdown](https://streamdown.ai) and can be used standalone in any streaming Markdown application.

## Features

- 🔄 **Streaming-optimized** - Handles incomplete Markdown gracefully
- 🎨 **Smart completion** - Auto-closes bold, italic, code, links, images, strikethrough, and math blocks
- ⚡ **Performance-first** - Optimized string operations, no regex allocations
- 🛡️ **Context-aware** - Respects code blocks, math blocks, and nested formatting
- 🎯 **Edge case handling** - List markers, word-internal characters, escaped sequences
- 📦 **Zero dependencies** - Pure TypeScript implementation

## Supported Syntax

Remend intelligently completes the following incomplete Markdown patterns:

- **Bold**: `**text` → `**text**`
- **Italic**: `*text` or `_text` → `*text*` or `_text_`
- **Bold + Italic**: `***text` → `***text***`
- **Inline code**: `` `code `` → `` `code` ``
- **Strikethrough**: `~~text` → `~~text~~`
- **Links**: `[text](url` → `[text](streamdown:incomplete-link)`
- **Images**: `![alt](url` → removed (can't display partial images)
- **Block math**: `$$formula` → `$$formula$$`
- **Inline math**: `$formula` → `$formula$` (opt-in, see `inlineKatex`)
- **Single tilde escape**: `20~25` → `20\~25` (prevents false strikethrough)

## Installation

```bash
npm i remend
```

## Usage

```typescript
import remend from "remend";

// During streaming
const partialMarkdown = "This is **bold text";
const completed = remend(partialMarkdown);
// Result: "This is **bold text**"

// With incomplete link
const partialLink = "Check out [this link](https://exampl";
const completed = remend(partialLink);
// Result: "Check out [this link](streamdown:incomplete-link)"
```

### Configuration

You can selectively disable specific completions by passing an options object. Options default to `true` unless noted otherwise:

```typescript
import remend from "remend";

// Disable link and KaTeX completion
const completed = remend(partialMarkdown, {
  links: false,
  katex: false,
});
```

Available options:

| Option | Description |
|--------|-------------|
| `links` | Complete incomplete links |
| `images` | Complete incomplete images |
| `bold` | Complete bold formatting (`**`) |
| `italic` | Complete italic formatting (`*` and `_`) |
| `boldItalic` | Complete bold-italic formatting (`***`) |
| `inlineCode` | Complete inline code formatting (`` ` ``) |
| `singleTilde` | Escape single `~` between word characters to prevent false strikethrough (e.g. `20~25`) |
| `strikethrough` | Complete strikethrough formatting (`~~`) |
| `katex` | Complete block KaTeX math (`$$`) |
| `inlineKatex` | Complete inline KaTeX math (`$`) — defaults to `false` to avoid ambiguity with currency symbols |
| `setextHeadings` | Handle incomplete setext headings |
| `handlers` | Custom handlers to extend remend |

### Custom Handlers

You can extend remend with custom handlers to complete your own markers during streaming. This is useful for custom syntax like `<<<JOKE>>>` blocks or other domain-specific patterns.

```typescript
import remend, { type RemendHandler } from "remend";

const jokeHandler: RemendHandler = {
  name: "joke",
  handle: (text) => {
    // Complete <<<JOKE>>> marks that aren't closed
    const match = text.match(/<<<JOKE>>>([^<]*)$/);
    if (match && !text.endsWith("<<</JOKE>>>")) {
      return `${text}<<</JOKE>>>`;
    }
    return text;
  },
  priority: 80, // Runs after most built-ins (0-70)
};

const result = remend(content, { handlers: [jokeHandler] });
```

#### Handler Interface

```typescript
interface RemendHandler {
  name: string;                    // Unique identifier
  handle: (text: string) => string; // Transform function
  priority?: number;               // Lower runs first (default: 100)
}
```

#### Built-in Priorities

Built-in handlers use priorities 0-75. Custom handlers default to 100 (run after built-ins):

| Handler | Priority |
|---------|----------|
| `singleTilde` | 0 |
| `comparisonOperators` | 5 |
| `htmlTags` | 10 |
| `setextHeadings` | 15 |
| `links` | 20 |
| `boldItalic` | 30 |
| `bold` | 35 |
| `italic` | 40-42 |
| `inlineCode` | 50 |
| `strikethrough` | 60 |
| `katex` | 70 |
| `inlineKatex` | 75 |
| Custom (default) | 100 |

#### Exported Utilities

Remend exports utility functions for context detection in custom handlers:

```typescript
import {
  isWithinCodeBlock,
  isWithinMathBlock,
  isWithinLinkOrImageUrl,
  isWordChar,
} from "remend";

const handler: RemendHandler = {
  name: "custom",
  handle: (text) => {
    // Skip if we're inside a code block
    if (isWithinCodeBlock(text, text.length - 1)) {
      return text;
    }
    // Your logic here
    return text;
  },
};
```

### Usage with Remark

Remend is a preprocessor that must be run on the raw Markdown string **before** passing it into the unified/remark processing pipeline:

```typescript
import remend from "remend";
import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import rehypeStringify from "rehype-stringify";

const streamedMarkdown = "This is **incomplete bold";

// Run Remend first to complete incomplete syntax
const completedMarkdown = remend(streamedMarkdown);

// Then process with unified
const file = await unified()
  .use(remarkParse)
  .use(remarkRehype)
  .use(rehypeStringify)
  .process(completedMarkdown);

console.log(String(file));
```

This is important because Remend operates on the raw string level, while remark/unified work with abstract syntax trees (ASTs). Running Remend after parsing would be ineffective.

## How It Works

Remend analyzes the input text and:

1. Detects incomplete formatting markers at the end of the text
2. Counts opening vs closing markers (considering escaped characters)
3. Intelligently adds closing markers when needed
4. Respects context like code blocks, math blocks, and list items
5. Handles edge cases like nested brackets and word-internal characters

The parser is designed to be defensive and only completes formatting when it's unambiguous that the block is incomplete.

## Performance

Remend is built for high-performance streaming scenarios:

- Direct string iteration instead of regex splits
- ASCII fast-path for common characters
- Minimal memory allocations
- Early returns for common cases

For more info, see the [documentation](https://streamdown.ai/docs/termination).
