import json
import unittest

from agent_quality_lab.models import ScriptedModel
from agent_quality_lab.runtime import Agent, Completion, Tool, ToolCall, ToolError


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.writes = []
        self.tool = Tool("write", "test write", {"target": "target"}, self.write)

    def write(self, target):
        self.writes.append(target)
        return {"target": target}

    def call(self, identifier="c1", name="write", arguments='{"target":"a"}'):
        return ToolCall(identifier, name, arguments)

    def test_model_selects_tool_and_observes_result_before_answer(self):
        def answer(messages):
            self.assertEqual(json.loads(messages[-1]["content"]), {"ok": True, "data": {"target": "a"}})
            return Completion("done")
        agent = Agent(ScriptedModel([Completion(tool_calls=[self.call()]), answer]), [self.tool], "system")
        result = agent.run("request")
        self.assertEqual((result.status, result.model_calls, result.tool_calls), ("responded", 2, 1))
        self.assertEqual(self.writes, ["a"])
        self.assertEqual([event["sequence"] for event in agent.events], list(range(1, 5)))

    def test_bad_arguments_and_unavailable_approval_tool_have_no_side_effect(self):
        cases = [("write", "{broken", "invalid_arguments"),
                 ("write", '[]', "invalid_arguments"),
                 ("write", '{"target":"a","tenant_id":"tenant-b"}', "invalid_arguments"),
                 ("write", '{"target":null}', "invalid_arguments"),
                 ("write", '{"target":" "}', "invalid_arguments"),
                 ("approve", '{}', "unknown_tool")]
        for name, arguments, code in cases:
            with self.subTest(arguments=arguments, name=name):
                agent = Agent(ScriptedModel([Completion(tool_calls=[self.call(name=name, arguments=arguments)]), Completion("blocked")]),
                              [self.tool], "system")
                self.assertEqual(agent.run("request").status, "responded")
                output = next(event["output"] for event in agent.events if event["event"] == "tool_result")
                self.assertEqual(output["error"]["code"], code)
        self.assertFalse(self.writes)

    def test_tool_budget_rejects_whole_batch_before_side_effects(self):
        reply = Completion(tool_calls=[self.call("c1"), self.call("c2")])
        agent = Agent(ScriptedModel([reply]), [self.tool], "system", max_tool_calls=1)
        self.assertEqual(agent.run("request").status, "budget_exhausted")
        self.assertFalse(self.writes)

    def test_model_loop_stops_with_partial_effects_visible(self):
        agent = Agent(ScriptedModel([Completion(tool_calls=[self.call()])]), [self.tool], "system", max_model_calls=1)
        result = agent.run("request")
        self.assertEqual(result.status, "budget_exhausted")
        self.assertEqual(self.writes, ["a"])
        self.assertTrue(any(event["event"] == "tool_result" for event in agent.events))

    def test_duplicate_call_ids_cannot_repeat_write(self):
        reply = Completion(tool_calls=[self.call()])
        agent = Agent(ScriptedModel([reply, reply]), [self.tool], "system")
        self.assertEqual(agent.run("request").status, "model_error")
        self.assertEqual(self.writes, ["a"])

    def test_duplicate_ids_within_batch_rejected_before_write(self):
        agent = Agent(ScriptedModel([Completion(tool_calls=[self.call(), self.call()])]), [self.tool], "system")
        self.assertEqual(agent.run("request").status, "model_error")
        self.assertFalse(self.writes)

    def test_model_failure_and_empty_answer_are_explicit(self):
        for replies in ([], [Completion()]):
            with self.subTest(replies=replies):
                agent = Agent(ScriptedModel(replies), [self.tool], "system")
                self.assertEqual(agent.run("request").status, "model_error")
                self.assertEqual(agent.events[-1]["event"], "model_error")

    def test_internal_tool_error_does_not_expose_exception_text(self):
        def fail():
            raise RuntimeError("private-diagnostic-value")
        tool = Tool("write", "test", {}, fail)
        agent = Agent(ScriptedModel([Completion(tool_calls=[self.call(arguments="{}")]), Completion("failed")]), [tool], "system")
        agent.run("request")
        self.assertNotIn("private-diagnostic-value", json.dumps(agent.events))
        self.assertIn("tool_internal_error", json.dumps(agent.events))

    def test_reasoning_roundtrip_is_preserved_but_not_exported(self):
        def answer(messages):
            self.assertEqual(messages[-2]["reasoning_content"], "private-reasoning")
            return Completion("done")
        first = Completion(tool_calls=[self.call()], reasoning_content="private-reasoning")
        agent = Agent(ScriptedModel([first, answer]), [self.tool], "system")
        self.assertEqual(agent.run("request").status, "responded")
        self.assertNotIn("private-reasoning", json.dumps(agent.events))

    def test_tool_business_rejection_is_preserved(self):
        def denied():
            raise ToolError("forbidden", "denied")
        agent = Agent(ScriptedModel([Completion(tool_calls=[self.call(arguments="{}")]), Completion("denied")]),
                      [Tool("write", "test", {}, denied)], "system")
        agent.run("request")
        output = next(event["output"] for event in agent.events if event["event"] == "tool_result")
        self.assertEqual(output, {"ok": False, "error": {"code": "forbidden", "message": "denied"}})
