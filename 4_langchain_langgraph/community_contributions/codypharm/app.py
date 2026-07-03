import gradio as gr
from sidekick import Sidekick, DEFAULT_SUCCESS_CRITERIA

# -------------------------------------------------------------------------
#  Helper: build nice readable message from form fields
# -------------------------------------------------------------------------
def build_prescription_message(
    age, weight_kg, gender, is_pregnant,
    renal_status, allergies, concurrent_medications,
    drug_name, strength_dose, route, frequency, duration_days, indication
):
    if not drug_name.strip():
        return "Please enter at least the drug name."

    lines = ["Please perform full clinical validation of this prescription."]

    # Patient section
    patient_parts = []
    if age is not None:
        patient_parts.append(f"{int(age)} years old")
    if weight_kg is not None:
        patient_parts.append(f"{weight_kg} kg")
    if gender:
        patient_parts.append(gender.lower())
    if is_pregnant:
        patient_parts.append("pregnant")

    if patient_parts:
        lines.append("Patient: " + ", ".join(patient_parts) + ".")

    if renal_status and renal_status.strip().lower() not in ["normal", ""]:
        lines.append(f"Renal function: {renal_status.strip()}")

    if allergies and allergies.strip().lower() not in ["none", ""]:
        lines.append(f"Allergies: {allergies.strip()}")

    if concurrent_medications and concurrent_medications.strip().lower() not in ["none", ""]:
        lines.append(f"Concurrent medications: {concurrent_medications.strip()}")

    # Prescription
    lines.append("")
    lines.append("Prescription:")
    lines.append(f"• Drug: **{drug_name.strip()}**")
    if strength_dose:
        lines.append(f"• Dose / strength: {strength_dose.strip()}")
    if route:
        lines.append(f"• Route: {route.strip()}")
    if frequency:
        lines.append(f"• Frequency: {frequency.strip()}")
    if duration_days is not None:
        lines.append(f"• Duration: {duration_days} day{'s' if duration_days != 1 else ''}")
    if indication:
        lines.append(f"• Indication: {indication.strip()}")

    lines.append("")
    lines.append("Please run all appropriate checks:")
    lines.append("• allergies & cross-reactivity")
    lines.append("• drug–drug interactions")
    lines.append("• duplicate therapy")
    lines.append("• dosing (weight / age / renal / hepatic / geriatric / pediatric)")
    lines.append("• pregnancy / lactation safety (if applicable)")
    lines.append("• recent recalls / shortages")
    lines.append("")
    lines.append("Then give a clear **Dispense** / **Do Not Dispense** decision with structured reasoning and pharmacist recommendations.")

    return "\n".join(lines)


async def process_message(sidekick, user_message: str, success_criteria: str, chat_history):
    if sidekick is None:
        return chat_history + [{"role": "assistant", "content": "⚠️ Sidekick not initialized."}], sidekick

    if not user_message or not user_message.strip():
        return chat_history, sidekick   # ignore empty submits

    try:
        updated_history, updated_sidekick = await sidekick.run_superstep(
            message=user_message,
            success_criteria=success_criteria,
            history=chat_history
        )
        return updated_history, updated_sidekick

    except Exception as e:
        import traceback
        msg = f"**Processing error**\n\n```python\n{traceback.format_exc()}\n```"
        return chat_history + [{"role": "assistant", "content": msg}], sidekick

# -------------------------------------------------------------------------
#  Quick-fill demo prescriptions
# -------------------------------------------------------------------------
def load_pediatric_example():
    return (
        build_prescription_message(4, 18.5, "Male", False, "Normal", "None known", "None",
                                   "Amoxicillin", "250 mg / 5 mL suspension", "oral", "8-hourly", 7, "acute otitis media"),
        DEFAULT_SUCCESS_CRITERIA,
        4, 18.5, "Male", False, "Normal", "None known", "None",
        "Amoxicillin", "250 mg / 5 mL suspension", "oral", "8-hourly", 7, "acute otitis media"
    )


def load_geriatric_renal_example():
    return (
        build_prescription_message(81, 58, "Female", False, "eGFR 34 mL/min/1.73m²", "ACE-inhibitor angioedema", "Amlodipine 5 mg daily, Paracetamol PRN",
                                   "Ibuprofen", "400 mg tablet", "oral", "8-hourly PRN", None, "osteoarthritis pain"),
        DEFAULT_SUCCESS_CRITERIA,
        81, 58, "Female", False, "eGFR 34 mL/min/1.73m²", "ACE-inhibitor angioedema", "Amlodipine 5 mg daily, Paracetamol PRN",
        "Ibuprofen", "400 mg tablet", "oral", "8-hourly PRN", None, "osteoarthritis pain"
    )


def load_pregnancy_example():
    return (
        build_prescription_message(28, 74, "Female", True, "Normal", "NKDA", "Folic acid 800 mcg daily, Levothyroxine 100 mcg daily",
                                   "Metoclopramide", "10 mg tablet", "oral", "8-hourly PRN", 3, "hyperemesis"),
        DEFAULT_SUCCESS_CRITERIA,
        28, 74, "Female", True, "Normal", "NKDA", "Folic acid 800 mcg daily, Levothyroxine 100 mcg daily",
        "Metoclopramide", "10 mg tablet", "oral", "8-hourly PRN", 3, "hyperemesis"
    )


def load_allergy_example():
    return (
        build_prescription_message(53, 92, "Male", False, "Normal", "Penicillin – anaphylaxis 1998", "Atorvastatin 40 mg nocte, Metformin XR 1 g BD",
                                   "Cefalexin", "500 mg capsule", "oral", "6-hourly", 7, "cellulitis"),
        DEFAULT_SUCCESS_CRITERIA,
        53, 92, "Male", False, "Normal", "Penicillin – anaphylaxis 1998", "Atorvastatin 40 mg nocte, Metformin XR 1 g BD",
        "Cefalexin", "500 mg capsule", "oral", "6-hourly", 7, "cellulitis"
    )


# -------------------------------------------------------------------------
#  Gradio interface
# -------------------------------------------------------------------------
with gr.Blocks(title="Pharmacy Sidekick — Prescription Checking Assistant") as demo:

    gr.Markdown("# 🩺 Pharmacy Sidekick")
    gr.Markdown("AI-assisted prescription validation / clinical checking support tool")

    sidekick_state = gr.State()

    with gr.Row():

        # ────────────────────────────────────────────────
        # Left column – Input form
        # ────────────────────────────────────────────────
        with gr.Column(scale=4):

            with gr.Group():
                gr.Markdown("### Patient")
                with gr.Row():
                    age = gr.Number(label="Age (years)", minimum=0, maximum=120, step=1, value=None)
                    weight = gr.Number(label="Weight (kg)", minimum=1, maximum=300, step=0.1, value=None)
                    gender = gr.Dropdown(["Male", "Female", "Non-binary / other"], label="Sex", value=None)
                is_pregnant = gr.Checkbox(label="Currently pregnant / <12 weeks postpartum", value=False)

                renal = gr.Textbox(label="Renal function", placeholder="e.g. eGFR 52, CrCl 38, dialysis, normal", value="Normal")
                allergies = gr.Textbox(label="Allergies / ADRs", placeholder="e.g. penicillin – anaphylaxis, sulfa – rash", value="None known")
                other_meds = gr.Textbox(label="Other regular medicines", lines=2,
                                        placeholder="e.g. metformin 1 g BD, candesartan 16 mg mane, paracetamol PRN")

            with gr.Group():
                gr.Markdown("### Prescription")
                with gr.Row():
                    drug = gr.Textbox(label="Drug name", placeholder="e.g. amoxicillin, apixaban", scale=3)
                    strength = gr.Textbox(label="Strength / dose", placeholder="e.g. 500 mg, 250 mg/5 mL", scale=2)
                with gr.Row():
                    route = gr.Dropdown(["oral", "IV", "IM", "SC", "inhaled", "topical", "rectal", "other"],
                                        label="Route", value="oral", scale=1)
                    freq = gr.Textbox(label="Frequency", placeholder="e.g. BD, TDS, 8-hourly, once daily", scale=2)
                    duration = gr.Number(label="Duration (days)", minimum=0, step=1, value=None, scale=1)

                indication = gr.Textbox(label="Indication / reason", placeholder="e.g. community-acquired pneumonia, post-operative nausea", lines=1)

            prompt_preview = gr.Textbox(
                label="Message that will be sent to Sidekick",
                lines=9,
                interactive=True,
                value="(click \"Generate message\" or fill fields above)"
            )

            with gr.Row():
                generate_btn = gr.Button("Generate message from fields", variant="secondary")
                send_btn = gr.Button("Send → Sidekick", variant="primary", scale=2)

        # ────────────────────────────────────────────────
        # Right column – Chat
        # ────────────────────────────────────────────────
        with gr.Column(scale=7):
            chatbot = gr.Chatbot(height=620, show_label=False)
            criteria = gr.Textbox(
                label="Evaluation / success criteria",
                value=DEFAULT_SUCCESS_CRITERIA,
                lines=5,
                interactive=True
            )
            with gr.Row():
                clear_btn = gr.Button("Clear chat", variant="stop")
                reset_all_btn = gr.Button("Reset everything", variant="secondary")

    # ────────────────────────────────────────────────
    # Quick load buttons
    # ────────────────────────────────────────────────
    with gr.Accordion("Quick-load test cases", open=False):
        with gr.Row():
            gr.Button("4 yo – amoxicillin otitis", variant="secondary").click(
                load_pediatric_example,
                outputs=[prompt_preview, criteria, age, weight, gender, is_pregnant, renal, allergies, other_meds,
                         drug, strength, route, freq, duration, indication]
            )
            gr.Button("81 yo – ibuprofen + renal impairment", variant="secondary").click(
                load_geriatric_renal_example,
                outputs=[prompt_preview, criteria, age, weight, gender, is_pregnant, renal, allergies, other_meds,
                         drug, strength, route, freq, duration, indication]
            )
            gr.Button("28 yo pregnant – metoclopramide", variant="secondary").click(
                load_pregnancy_example,
                outputs=[prompt_preview, criteria, age, weight, gender, is_pregnant, renal, allergies, other_meds,
                         drug, strength, route, freq, duration, indication]
            )
            gr.Button("53 yo – cefalexin + penicillin anaphylaxis", variant="secondary").click(
                load_allergy_example,
                outputs=[prompt_preview, criteria, age, weight, gender, is_pregnant, renal, allergies, other_meds,
                         drug, strength, route, freq, duration, indication]
            )

    # ────────────────────────────────────────────────
    # Event handlers
    # ────────────────────────────────────────────────
    generate_btn.click(
        build_prescription_message,
        inputs=[age, weight, gender, is_pregnant, renal, allergies, other_meds,
                drug, strength, route, freq, duration, indication],
        outputs=prompt_preview
    )

    # Assuming you have these async functions already defined in your code
    send_btn.click(
        fn=process_message,
        inputs=[sidekick_state, prompt_preview, criteria, chatbot],
        outputs=[chatbot, sidekick_state]
    )

    prompt_preview.submit(
        fn=process_message,
        inputs=[sidekick_state, prompt_preview, criteria, chatbot],
        outputs=[chatbot, sidekick_state]
    )

    clear_btn.click(
        lambda: ([], []),
        outputs=[chatbot, prompt_preview]
    )

    reset_all_btn.click(
        lambda: (None, DEFAULT_SUCCESS_CRITERIA, None, None, None, False, None, None, None, None, None, None, None, None, None, [], None),
        outputs=[age, criteria, weight, gender, is_pregnant, renal, allergies, other_meds,
                 drug, strength, route, freq, duration, indication, prompt_preview, chatbot, sidekick_state]
    )

    # Load Sidekick on startup
    demo.load(lambda: Sidekick(), outputs=sidekick_state)


if __name__ == "__main__":
    demo.launch(
        theme=gr.themes.Default(primary_hue="emerald"),
        inbrowser=True,
        
    )