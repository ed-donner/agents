from models.schema import GenerateRecommendationsInput, GenerateRecommendationsOutput, Recommendation

def generate_recommendations(input: GenerateRecommendationsInput) -> GenerateRecommendationsOutput:
    recommendations = []
    for gap in input.gaps:
        recommendations.append(
            Recommendation(
                action=f"Add step: '{gap.step}'",
                reason=f"This step is recommended as '{gap.priority}' priority by industry standards.",
                impact="Reduces operational risk and improves process quality."
            )
        )
    return GenerateRecommendationsOutput(recommendations=recommendations)