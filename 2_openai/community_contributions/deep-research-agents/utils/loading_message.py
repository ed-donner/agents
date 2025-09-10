loading_html = """
<span style="font-style: italic; color: gray;">
  Generating response
  <span class="dot" style="
      display:inline-block;
      width:5px;
      animation: blink 1s infinite;
    ">.</span>
  <span class="dot" style="
      display:inline-block;
      width:5px;
      animation: blink 1s infinite 0.2s;
    ">.</span>
  <span class="dot" style="
      display:inline-block;
      width:5px;
      animation: blink 1s infinite 0.4s;
    ">.</span>
</span>

<style>
@keyframes blink {
  0%, 20% { opacity: 0; }
  50% { opacity: 1; }
  100% { opacity: 0; }
}
</style>
"""
