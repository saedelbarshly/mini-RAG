import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from controllers.NLPController import NLPController


class NLPQueryRewritingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.controller = NLPController.__new__(NLPController)
        self.controller.logger = Mock()
        self.controller.template_parser = Mock()
        self.controller.template_parser.get.return_value = "Rewrite the query."
        self.controller.generation_client = Mock()
        self.controller.generation_client.enums = SimpleNamespace(
            SYSTEM=SimpleNamespace(value="system")
        )
        self.controller.generation_client.construct_prompt.side_effect = (
            lambda prompt, role: {"role": role, "content": prompt}
        )

    def test_rewrite_query_includes_conversation_history(self):
        self.controller.generation_client.generate_text.return_value = (
            "Standalone query"
        )

        rewritten = self.controller.rewrite_query(
            "What about its limitations?",
            [{"role": "user", "content": "Tell me about product X."}]
        )

        self.assertEqual(rewritten, "Standalone query")
        self.controller.generation_client.generate_text.assert_called_once_with(
            prompt="What about its limitations?",
            chat_history=[
                {"role": "system", "content": "Rewrite the query."},
                {"role": "user", "content": "Tell me about product X."}
            ],
            temperature=0
        )

    async def test_answer_retrieves_with_rewritten_query(self):
        self.controller.rewrite_query = Mock(return_value="Standalone query")
        self.controller.search_vector_db_collection = AsyncMock(
            return_value=[SimpleNamespace(text="Document text")]
        )
        def get_prompt(group, key, variables=None):
            if key == "system_prompt":
                return "Answer from context."
            if key == "document_prompt":
                return variables["chunk_text"]
            return variables["query"]

        self.controller.template_parser.get.side_effect = get_prompt
        self.controller.generation_client.enums = SimpleNamespace(
            SYSTEM=SimpleNamespace(value="system")
        )
        self.controller.generation_client.process_text.return_value = "Document text"
        self.controller.generation_client.generate_text.return_value = "Answer"

        result = await self.controller.answer_rag_question(
            project=SimpleNamespace(id=1),
            query="What about its limitations?",
            chat_history=[{"role": "user", "content": "Tell me about product X."}]
        )

        self.controller.search_vector_db_collection.assert_awaited_once_with(
            project=SimpleNamespace(id=1),
            text="Standalone query",
            limit=10
        )
        self.controller.rewrite_query.assert_called_once_with(
            query="What about its limitations?",
            chat_history=[{"role": "user", "content": "Tell me about product X."}]
        )
        self.assertEqual(result[0], "Answer")
        self.assertEqual(result[3], "Standalone query")


if __name__ == "__main__":
    unittest.main()
