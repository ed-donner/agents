from fastmcp import FastMCP

import re

plag = FastMCP("plagiarism")

@plag.tool()
def suspicious_ngrams(text: str, n: int = 10, top_k: int = 5) -> dict:
    words = re.findall(r"[A-Za-z0-9']+", text.lower())
    grams = [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]
    from collections import Counter
    top = Counter(grams).most_common(top_k)
    return {"n": n, "top": top}

if __name__ == "__main__":
    plag.run("stdio")