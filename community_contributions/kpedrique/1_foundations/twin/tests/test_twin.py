"""Offline regression tests; no model requests or notifications are sent."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from openai.types.chat import ChatCompletionMessage

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
import context
import retrieval


def response(content=None, tool_calls=None, finish_reason="stop", refusal=None):
    message = ChatCompletionMessage(
        role="assistant", content=content, tool_calls=tool_calls, refusal=refusal,
    )
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=finish_reason)])


def tool_response(call_id):
    return response(tool_calls=[{
        "id": call_id, "type": "function", "function": {
            "name": "record_unknown_question",
            "arguments": json.dumps({"question": "Expected salary?"}),
        },
    }], finish_reason="tool_calls")


def verdict(approved, feedback="", out_of_scope=False):
    return response(json.dumps({"approved": approved, "out_of_scope": out_of_scope, "feedback": feedback}))


def contact_response(*emails, prefix="contact"):
    return response(tool_calls=[{
        "id": f"{prefix}-{index}", "type": "function", "function": {
            "name": "record_user_details", "arguments": json.dumps({"email": email}),
        },
    } for index, email in enumerate(emails)], finish_reason="tool_calls")


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        # Synthetic facts keep tests independent of private docs and remote URLs.
        questions = {
            "en": ["What is your English level?", "When did Lupai start?",
                   "What did you build at Lupai?", "What cloud experience do you have?"],
            "es": ["¿Cuál es tu nivel de inglés?", "¿Cuándo empezó Lupai?",
                   "¿Qué construiste en Lupai?", "¿Qué experiencia tienes en cloud?"],
        }
        ids = ["ingles", "lupai", "lupai_stack", "cloud"]
        answers = ["English communication and fluency practice / inglés.",
                   "El proyecto de prueba empezó en junio de 2024.",
                   "Construí servicios FastAPI y un widget React en Lupai.",
                   "Cloud experience with AWS and Azure."]
        def read_document(filename, env_var):
            language = "en" if filename.endswith("_en.json") else "es"
            return json.dumps({
                "language": language,
                "review_notes": ["Internal note"],
                "pending_questions": [{"id": "salario", "answer": None}],
                "faqs": [{"id": key, "question": question, "answer": answer}
                         for key, question, answer in zip(ids, questions[language], answers)],
            }).encode()
        source = patch.object(retrieval, "read_document", side_effect=read_document)
        source.start()
        self.addCleanup(source.stop)
        retrieval.load_faqs.cache_clear()
        self.addCleanup(retrieval.load_faqs.cache_clear)

    def test_english_and_accented_spanish_find_same_fact(self):
        for query in ["¿Cuál es tu nivel de inglés?", "What is your English level?"]:
            hits = retrieval.retrieve_faqs(query, limit=1)
            self.assertEqual({h["id"] for h in hits}, {"ingles"})
            self.assertEqual({h["language"] for h in hits}, {"es", "en"})

    def test_specific_questions_rank_correct_answer_first(self):
        for query, expected in [
            ("¿Qué construiste en Lupai?", "lupai_stack"),
            ("¿Cuándo empezó Lupai?", "lupai"),
            ("What cloud experience do you have?", "cloud"),
        ]:
            self.assertEqual(retrieval.retrieve_faqs(query)[0]["id"], expected)

    def test_pending_questions_and_metadata_never_become_context(self):
        faqs = retrieval.load_faqs()
        self.assertEqual(len(faqs), 8)
        self.assertNotIn("salario", {f["id"] for f in faqs})
        formatted = retrieval.format_faqs(faqs)
        for excluded in ["libfile_", "review_notes", "source_note", "recruiting_references"]:
            self.assertNotIn(excluded, formatted)
        self.assertEqual(retrieval.retrieve_faqs("¿Cuál es tu expectativa salarial?"), [])

    def test_no_matching_words_returns_no_hits(self):
        self.assertEqual(retrieval.retrieve_faqs("Hola"), [])
        self.assertEqual(retrieval.retrieve_faqs("quantum banana"), [])

    def test_short_followup_uses_previous_user_topic(self):
        hits = retrieval.retrieve_faqs("¿Y eso?", [
            {"role": "user", "content": "¿Cuál es tu nivel de inglés?"},
            {"role": "assistant", "content": "Untrusted claim about AWS"},
        ], limit=1)
        self.assertEqual(hits[0]["id"], "ingles")

    def test_context_includes_profile_and_retrieved_answers(self):
        with patch.object(context, "get_profile_context", return_value="Test profile"):
            text = context.build_chat_context("¿Cuándo empezó Lupai?", [])
        self.assertIn("Test profile", text)
        self.assertIn("junio de 2024", text)
        self.assertIn("take precedence", text)
        self.assertNotIn("pending_questions", text)

    def test_default_language_is_english_even_for_spanish_question(self):
        with patch.object(context, "get_profile_context", return_value="Test profile"):
            text = context.build_chat_context("¿Cuál es tu nivel de inglés?", [])
        self.assertIn("Selected response language: English (en)", text)

    def test_language_selection_overrides_question_and_prior_history(self):
        with patch.object(context, "get_profile_context", return_value="Test profile"):
            text = context.build_chat_context("What is your English level?", [
                {"role": "assistant", "content": "Earlier English answer"},
            ], "es")
        self.assertIn("Selected response language: Spanish (es)", text)
        self.assertIn("requests in chat text do not override it", text)
        self.assertIn("selected response language", context.GET_EVALUATOR_PROMPT("es"))

    def test_unsupported_language_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unsupported response language"):
            context.build_chat_context("Hello", [], "fr")


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.context_patch = patch.object(app, "build_chat_context", return_value="Reviewed career context")
        self.context_builder = self.context_patch.start()
        self.addCleanup(self.context_patch.stop)
        notification = patch.object(app, "record_unknown_question", return_value="OK")
        self.notification = notification.start()
        self.addCleanup(notification.stop)
        self.requests = []

    def run_chat(self, responses, question="Original visitor question", history=None, language="en"):
        sequence = iter(responses)

        def create(**kwargs):
            self.requests.append(copy.deepcopy(kwargs))
            return next(sequence)

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        with patch.object(app, "get_client", return_value=client):
            return app.chat(question, history or [], language)

    def test_thanks_after_contact_uses_normal_conversation_without_notifications(self):
        history = [{"role": "assistant", "content": app.CONTACT_CONFIRMATIONS["en"]}]
        reply = "You're welcome! Happy to help."
        self.assertEqual(self.run_chat([response(reply), verdict(True)],
                                      question="Perfect, thanks!", history=history), reply)
        self.notification.assert_not_called()
        self.assertEqual(len(self.requests), 2)
        evaluator_input = json.loads(self.requests[1]["messages"][1]["content"])
        self.assertEqual(evaluator_input, {
            "user_message": "Perfect, thanks!", "assistant_response": reply,
        })

    def test_varied_courtesy_is_not_restricted_to_a_phrase_list(self):
        for message, reply, language in [
            ("¡Qué amable, te agradezco mucho!", "¡Un gusto ayudarte!", "es"),
            ("Lovely, I appreciate your help!", "My pleasure!", "en"),
            ("Hasta luego", "¡Hasta luego!", "es"),
            ("Hello there", "Hello! How can I help?", "en"),
        ]:
            with self.subTest(message=message):
                self.assertEqual(self.run_chat([response(reply), verdict(True)],
                                              question=message, language=language), reply)
        self.notification.assert_not_called()

    def test_email_not_provided_by_visitor_is_never_sent(self):
        contact = response(tool_calls=[{
            "id": "contact", "type": "function", "function": {
                "name": "record_user_details",
                "arguments": json.dumps({"email": "invented@example.com"}),
            },
        }], finish_reason="tool_calls")
        with patch.object(app, "handle_tool_calls") as handler:
            result = self.run_chat([contact], question="Mi correo es actual@example.com")
        handler.assert_not_called()
        self.assertNotEqual(result, app.CONTACT_CONFIRMATIONS["en"])

    def test_tool_failure_result_is_never_treated_as_success(self):
        with patch.object(app, "handle_tool_calls", return_value=[{"content": '"FAILED"'}]):
            result = self.run_chat([tool_response("failure")])
        self.assertIn("couldn't record", result)
        self.notification.assert_not_called()

    def test_evaluator_only_receives_latest_pair_and_selected_language(self):
        client = Mock()
        client.chat.completions.create.return_value = verdict(True)
        with patch.object(app, "get_client", return_value=client):
            app.evaluate_response("Muchas gracias", "De nada", "es")
        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(json.loads(request["messages"][1]["content"]), {
            "user_message": "Muchas gracias", "assistant_response": "De nada",
        })
        self.assertIn("Spanish", request["messages"][0]["content"])

    def test_selected_language_is_forwarded_for_each_turn(self):
        self.run_chat([response("Hello"), verdict(True)])
        self.context_builder.assert_called_with("Original visitor question", [], "en")
        self.run_chat([response("Hola"), verdict(True)], language="es")
        self.context_builder.assert_called_with("Original visitor question", [], "es")


    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_email_followup_with_gradio_history_records_contact(self, handler):
        history = [{"role": "assistant", "metadata": None, "options": None,
                    "content": [{"type": "text", "text": "Déjame tu correo para contactarte."}]}]
        contact = response(tool_calls=[{
            "id": "contact", "type": "function", "function": {
                "name": "record_user_details",
                "arguments": json.dumps({"email": "test@example.com"}),
            },
        }], finish_reason="tool_calls")
        result = self.run_chat([
            contact, response("Gracias, registré tu correo."), verdict(True),
        ], question="Claro, mi email es test@example.com", history=history, language="es")
        self.assertEqual(result, app.CONTACT_CONFIRMATIONS["es"])
        self.assertEqual(len(self.requests), 1)
        handler.assert_called_once()
        self.assertEqual(handler.call_args.args[0][0].function.name, "record_user_details")
        self.assertEqual(self.requests[0]["messages"][1], {
            "role": "assistant", "content": "Déjame tu correo para contactarte.",
        })
        self.context_builder.assert_called_with("Claro, mi email es test@example.com", [{
            "role": "assistant", "content": "Déjame tu correo para contactarte.",
        }], "es")
        self.notification.assert_not_called()


    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_successful_contact_is_acknowledged_without_model_evaluation(self, handler):
        contact = response(tool_calls=[{
            "id": "contact", "type": "function", "function": {
                "name": "record_user_details",
                "arguments": json.dumps({"email": "test@example.com"}),
            },
        }], finish_reason="tool_calls")
        result = self.run_chat([contact], question="Mi email es test@example.com", language="es")
        self.assertEqual(result, app.CONTACT_CONFIRMATIONS["es"])
        self.assertEqual(len(self.requests), 1)
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"Email already exists"'}])
    def test_existing_contact_is_acknowledged_without_evaluator_or_unknown_notification(self, handler):
        contact = response(tool_calls=[{
            "id": "contact", "type": "function", "function": {
                "name": "record_user_details",
                "arguments": json.dumps({"email": "test@example.com"}),
            },
        }], finish_reason="tool_calls")
        result = self.run_chat([contact], question="Mi email es test@example.com", language="es")
        self.assertEqual(result, app.EXISTING_CONTACT_CONFIRMATIONS["es"])
        self.assertEqual(len(self.requests), 1)
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", side_effect=TimeoutError("Notification unavailable"))
    def test_failed_contact_is_not_acknowledged_as_success(self, handler):
        contact = response(tool_calls=[{
            "id": "contact", "type": "function", "function": {
                "name": "record_user_details",
                "arguments": json.dumps({"email": "test@example.com"}),
            },
        }], finish_reason="tool_calls")
        result = self.run_chat([contact], question="Mi email es test@example.com", language="es")
        self.assertNotEqual(result, app.CONTACT_CONFIRMATIONS["es"])
        self.notification.assert_called_once()

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_two_emails_in_one_tool_batch_are_both_confirmed(self, handler):
        result = self.run_chat([contact_response("first@example.com", "second@example.com")],
                               question="Contact me at first@example.com, second@example.com")
        self.assertEqual(result, "Registered emails: first@example.com, second@example.com.")
        self.assertEqual(handler.call_count, 2)
        self.assertEqual(len(self.requests), 1)
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_sequential_tool_calls_continue_until_both_emails_are_registered(self, handler):
        result = self.run_chat([
            contact_response("first@example.com", prefix="first"),
            contact_response("second@example.com", prefix="second"),
        ], question="Contact me at first@example.com, second@example.com", language="es")
        self.assertEqual(result, "Correos registrados: first@example.com, second@example.com.")
        self.assertEqual(handler.call_count, 2)
        self.assertEqual(len(self.requests), 2)
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", side_effect=[
        [{"content": '"Email already exists"'}], [{"content": '"OK"'}],
    ])
    def test_mixed_existing_and_new_contacts_have_distinct_confirmation(self, handler):
        result = self.run_chat([contact_response("old@example.com", "new@example.com")],
                               question="Use old@example.com and new@example.com")
        self.assertIn("Registered emails: new@example.com.", result)
        self.assertIn("Already registered: old@example.com.", result)
        self.assertNotIn("No new notification was sent", result)
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", side_effect=[
        [{"content": '"OK"'}], TimeoutError("Second notification failed"),
    ])
    def test_partial_failure_does_not_claim_both_contacts_were_registered(self, handler):
        result = self.run_chat([contact_response("first@example.com", "second@example.com")],
                               question="Use first@example.com and second@example.com")
        self.assertIn("Registered emails: first@example.com.", result)
        self.assertIn("Not registered: second@example.com.", result)
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_model_omitting_second_contact_does_not_produce_false_confirmation(self, handler):
        result = self.run_chat([
            contact_response("first@example.com"), response("Both recorded"),
        ], question="Use first@example.com and second@example.com")
        self.assertIn("Registered emails: first@example.com.", result)
        self.assertIn("Not registered: second@example.com.", result)
        self.assertNotIn("Both recorded", result)
        self.notification.assert_not_called()

    def test_flat_messages_shared_context_original_question_and_history(self):
        history = [{"role": "user", "content": "Earlier topic"},
                   {"role": "assistant", "content": "Earlier answer"}]
        original = copy.deepcopy(history)
        self.assertEqual(self.run_chat([response("Candidate"), verdict(True)], history=history), "Candidate")
        request, evaluation = self.requests
        self.assertTrue(all(isinstance(m, dict) for m in request["messages"]))
        payload = json.loads(evaluation["messages"][1]["content"])
        self.assertEqual(payload["user_message"], "Original visitor question")
        self.assertEqual(set(payload), {"user_message", "assistant_response"})
        self.assertNotIn("Reviewed career context", evaluation["messages"][0]["content"])
        self.assertTrue(evaluation["response_format"]["json_schema"]["strict"])
        self.assertEqual(history, original)

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_tools_do_not_overwrite_user_question(self, handler):
        self.run_chat([tool_response("first"), response("Candidate"), verdict(True)])
        payload = json.loads(self.requests[-1]["messages"][1]["content"])
        self.assertEqual(payload["user_message"], "Original visitor question")
        self.assertNotIn("conversation", payload)
        handler.assert_called_once()

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_revision_processes_tools_and_is_evaluated_again(self, handler):
        result = self.run_chat([
            response("Unsupported salary"), verdict(False, "Do not invent a salary"),
            tool_response("revision-call"), response("I do not know"), verdict(True),
        ])
        self.assertEqual(result, "I do not know")
        handler.assert_called_once()
        self.assertEqual(json.loads(self.requests[-1]["messages"][1]["content"])["assistant_response"], result)

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_identical_tool_is_not_executed_twice_across_revisions(self, handler):
        self.run_chat([
            tool_response("first"), response("Candidate"), verdict(False, "Revise wording"),
            tool_response("second"), response("Revised"), verdict(True),
        ])
        handler.assert_called_once()
        tool_messages = [m for m in self.requests[-2]["messages"] if m["role"] == "tool"]
        self.assertEqual([m["tool_call_id"] for m in tool_messages], ["first", "second"])

    def test_rejected_candidates_are_never_returned(self):
        responses = [item for _ in range(app.MAX_REVISIONS + 1)
                     for item in [response("Bad answer"), verdict(False, "Unsupported")]]
        result = self.run_chat(responses)
        self.assertIn("Sorry, I can't answer", result)
        self.notification.assert_called_once_with("Original visitor question")
        self.assertEqual(len(self.requests), 2 * (app.MAX_REVISIONS + 1))

    def test_invalid_or_refused_evaluation_is_not_approval(self):
        for invalid in [response("not json"), response('{"approved": "true", "feedback": ""}'),
                        response('{"approved": true}'), response(refusal="Cannot evaluate")]:
            with self.subTest(invalid=invalid):
                result = self.run_chat([response("Candidate"), invalid])
                self.assertIn("Sorry, I can't answer", result)

    def test_truncated_generation_is_not_returned(self):
        result = self.run_chat([response("Partial", finish_reason="length")])
        self.assertIn("Sorry, I can't answer", result)

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_tool_loop_has_a_limit(self, handler):
        result = self.run_chat([tool_response(str(i)) for i in range(app.MAX_TOOL_ROUNDS + 1)])
        self.assertIn("Sorry, I can't answer", result)
        self.assertEqual(len(self.requests), app.MAX_TOOL_ROUNDS + 1)


    def test_personal_question_returns_professional_redirection_in_spanish(self):
        result = self.run_chat([
            response("Tengo dos hijos"), verdict(False, "Private facts", out_of_scope=True),
        ], question="Tienes hijos", language="es")
        self.assertIn("Solo puedo responder preguntas", result)
        self.assertNotIn("dos hijos", result)
        self.notification.assert_called_once_with("Tienes hijos")
        self.assertEqual(len(self.requests), 2)

    def test_valid_redirection_is_returned_for_personal_question_in_english(self):
        result = self.run_chat([
            response("I only answer professional questions"), verdict(True, out_of_scope=True),
        ], question="Tienes hijos", language="en")
        self.assertIn("I can only answer questions", result)
        self.notification.assert_called_once_with("Tienes hijos")

    def test_context_failure_returns_localized_fallback_and_records_question(self):
        self.context_builder.side_effect = OSError("Profile unavailable")
        result = app.chat("Pregunta de prueba", [], "es")
        self.assertEqual(result, "Lo siento, por ahora no puedo responder esa pregunta. "
                         "Tu pregunta ha sido registrada.")
        self.notification.assert_called_once_with("Pregunta de prueba")

    def test_model_failure_returns_fallback_and_records_question(self):
        with patch.object(app, "get_client", side_effect=TimeoutError("API unavailable")):
            result = app.chat("Question", [], "en")
        self.assertIn("Sorry, I can't answer", result)
        self.notification.assert_called_once_with("Question")

    def test_notification_failure_does_not_crash_or_claim_success(self):
        self.notification.side_effect = TimeoutError("Notification unavailable")
        result = self.run_chat([response("Candidate"), response("bad JSON")], language="es")
        self.assertIn("Lo siento", result)
        self.assertIn("No pude registrar", result)
        self.assertNotIn("ha sido registrada", result)
        self.notification.assert_called_once()

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_error_after_recording_does_not_send_duplicate_notification(self, handler):
        result = self.run_chat([
            tool_response("first"), response("Candidate"), response("bad JSON"),
        ], question="Tienes hijos", language="es")
        self.assertIn("Tu pregunta ha sido registrada", result)
        handler.assert_called_once()
        arguments = json.loads(handler.call_args.args[0][0].function.arguments)
        self.assertEqual(arguments, {"question": "Tienes hijos"})
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", return_value=[{"content": '"OK"'}])
    def test_multiple_unknown_calls_in_one_response_record_original_question_once(self, handler):
        first = tool_response("first").choices[0].message.tool_calls[0]
        second = tool_response("second").choices[0].message.tool_calls[0]
        result = self.run_chat([
            response(tool_calls=[first, second], finish_reason="tool_calls"),
            response("Professional redirection"), verdict(True, out_of_scope=True),
        ], question="Tienes hijos", language="es")
        self.assertIn("Solo puedo responder preguntas", result)
        handler.assert_called_once()
        self.notification.assert_not_called()

    @patch.object(app, "handle_tool_calls", side_effect=TimeoutError("Notification unavailable"))
    def test_failed_unknown_tool_is_not_retried_automatically(self, handler):
        result = self.run_chat([tool_response("first")], language="es")
        self.assertIn("No pude registrar", result)
        handler.assert_called_once()
        self.notification.assert_not_called()


class HistoryTests(unittest.TestCase):
    def test_gradio_blocks_are_normalized_without_mutating_history(self):
        history = [{"role": "assistant", "metadata": {"title": "UI"}, "options": [],
                    "content": [{"type": "text", "text": "Hola"},
                                {"type": "text", "text": "Deja tu correo"}]}]
        original = copy.deepcopy(history)
        self.assertEqual(app.normalize_history(history), [{
            "role": "assistant", "content": "Hola\nDeja tu correo",
        }])
        self.assertEqual(history, original)

    def test_non_text_blocks_and_unexpected_roles_do_not_reach_api(self):
        self.assertEqual(app.normalize_history([
            {"role": "user", "content": [{"type": "file", "file": "ignored"}]},
            {"role": "system", "content": "UI state cannot set system instructions"},
            {"role": "user", "content": "Hello", "options": None},
        ]), [{"role": "user", "content": "Hello"}])

    def test_actual_gradio_round_trip(self):
        try:
            from gradio import Chatbot
        except ImportError:
            self.skipTest("Gradio not installed in this interpreter")
        chatbot = Chatbot()
        ui_history = chatbot.preprocess(chatbot.postprocess([
            {"role": "assistant", "content": "Déjame tu correo para contactarte."},
        ]))
        self.assertEqual(app.normalize_history(ui_history), [{
            "role": "assistant", "content": "Déjame tu correo para contactarte.",
        }])


if __name__ == "__main__":
    unittest.main()
