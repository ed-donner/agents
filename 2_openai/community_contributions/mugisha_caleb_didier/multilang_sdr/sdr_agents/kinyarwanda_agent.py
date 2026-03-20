from agents import Agent
from core.openrouter import make_openrouter_model
from core.guardrails import block_competitor_mentions

INSTRUCTIONS = """Uri umuhanga mu gucuruza wandika imeri zo gushaka abakiriya bashya mu Kinyarwanda.

Ubonye ibisobanuro by'umukiriya ushobora kugura, andika imeri ikomeye, yihariye kandi ishishikaje:
- Tangira n'igitekerezo gikurura umuntu gifitanye isano n'umurimo cyangwa uruhare rw'umukiriya
- Sobanura neza agaciro k'ibyo utanga
- Shyiramo igikorwa cyoroshye umusaba gukora (urugero: ikiganiro cy'iminota 15)
- Koresha imvugo y'umwuga ariko ikunze
- Andika by'imvugo ngufi (munsi y'amagambo 200)

NTUKAVUGE izina ry'ibicuruzwa by'abahanganyi. Ibanda ku gaciro utanga gusa."""

kinyarwanda_model = make_openrouter_model("anthropic/claude-sonnet-4")

kinyarwanda_agent = Agent(
    name="Kinyarwanda Sales Agent",
    instructions=INSTRUCTIONS,
    model=kinyarwanda_model,
    output_guardrails=[block_competitor_mentions],
)
