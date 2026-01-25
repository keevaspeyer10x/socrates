"""MindsSolver - Multi-model collaboration solver for evaluation.

Queries multiple AI models in parallel, then synthesizes their responses
into a single answer using Claude as the synthesizer.

Supports model fallbacks (LEARNINGS recommendation) - when a primary model
fails, the solver can automatically try a fallback model.
"""

import asyncio
from typing import Any, Optional

from .base import Solver
from ..rate_limiter import RateLimiter


# Default models from multiminds (top 5)
DEFAULT_MODELS = [
    "anthropic/claude-opus-4-5-20251101",    # Claude Opus 4.5
    "google/gemini-3-pro-preview",            # Gemini 3 Pro
    "openai/gpt-5.2",                         # GPT-5.2
    "x-ai/grok-4.1-fast",                     # Grok 4.1
    "deepseek/deepseek-v3.2",                 # DeepSeek V3.2
]

# Default synthesizer model
DEFAULT_SYNTHESIZER = "anthropic/claude-opus-4-5-20251101"

# Model fallbacks for when primary models are unavailable (LEARNINGS recommendation)
# Maps primary model to fallback(s)
DEFAULT_FALLBACKS: dict[str, list[str]] = {
    "anthropic/claude-opus-4-5-20251101": ["anthropic/claude-sonnet-4-20250514"],
    "google/gemini-3-pro-preview": ["google/gemini-2.0-flash"],
    "openai/gpt-5.2": ["openai/gpt-4o"],
    "x-ai/grok-4.1-fast": ["x-ai/grok-3"],
    "deepseek/deepseek-v3.2": ["deepseek/deepseek-v3"],
}


SYNTHESIS_PROMPT = """You are synthesizing responses from multiple AI models to produce the best possible answer.

## Responses from different models:

{responses}

## Task:
Based on the above responses:
1. Identify the consensus across models
2. Resolve any disagreements by evaluating the reasoning
3. Extract the most accurate final answer

IMPORTANT FOR MULTIPLE CHOICE: If the question has letter choices (A, B, C, D), your answer MUST be ONLY the letter. Example: "ANSWER: C"
For other questions: "ANSWER: 42" or "ANSWER: The capital is Paris"

## Your synthesized answer:"""


# Truth-aware prompting for rigor mode
RIGOR_SYSTEM_PROMPT = """You are an AI assistant optimized for accuracy and epistemic calibration.

CRITICAL GUIDELINES:
1. NEVER fabricate information - if unsure, say "I don't know" or "I cannot verify"
2. Distinguish between: facts you're confident about, reasonable inferences, and speculation
3. For numerical claims, provide ranges rather than false precision
4. If citing sources, only cite ones you're certain exist
5. For contested topics, present multiple perspectives fairly

Your confidence should be well-calibrated: be confident when appropriate, uncertain when appropriate."""


# Cross-verification synthesis for deep mode
DEEP_SYNTHESIS_PROMPT = """You are integrating responses from multiple AI models with strict verification.

CRITICAL RULES:
1. CORROBORATION REQUIRED: Only include specific numbers, statistics, or citations if 2+ models agree
2. PRESERVE UNCERTAINTY: If models agree they can't verify something, preserve that honesty
3. TRUST CAUTION: If one model refuses to provide a figure but another does, trust the caution
4. CONTESTED TOPICS: Present both sides fairly when models genuinely disagree on opinion

## Model Responses:

{responses}

Based on the above, create an integrated response using ONLY corroborated claims.

IMPORTANT FOR MULTIPLE CHOICE: If the question has letter choices (A, B, C, D), your answer MUST be ONLY the letter. Example: "ANSWER: C"
For other questions: "ANSWER: 42" or "ANSWER: The capital is Paris"

## Your verified answer:"""


# Self-critique prompt for deep mode
SELF_CRITIQUE_PROMPT = """Review your previous response critically.

CHECK FOR:
1. Any claims that might be fabricated or unverifiable
2. Citations or sources that may not exist
3. Overconfident language where uncertainty would be more appropriate
4. Logical gaps or unsupported conclusions

YOUR PREVIOUS RESPONSE:
{response}

If you find issues, provide a CORRECTED response.
If it's solid, output it unchanged with a brief note confirming why it's sound.
Focus on substance, not just adding hedges.

End your response with:
ANSWER: <your final answer>"""


# Reasoning mode: explicit step-by-step reasoning with discussion
REASONING_QUERY_PROMPT = """Answer this question with explicit step-by-step reasoning.

REQUIREMENTS:
1. STATE YOUR APPROACH: Before solving, briefly explain your strategy
2. SHOW YOUR WORK: Walk through each step of your reasoning
3. IDENTIFY UNCERTAINTY: Flag any steps where you're less confident
4. CONCLUDE CLEARLY: End with your final answer

{question}

Think step by step:"""


REASONING_SYNTHESIS_PROMPT = """You are synthesizing responses from multiple AI models. Each model has provided step-by-step reasoning.

## Model Responses:

{responses}

## Your Task:

Analyze each model's reasoning carefully:

1. **COMPARE APPROACHES**: How did each model approach the problem? Were their strategies similar or different?

2. **EVALUATE REASONING STEPS**:
   - Which steps are sound across all models?
   - Where do models disagree? Analyze WHY they disagree.
   - Are there calculation errors, logical gaps, or different assumptions?

3. **IDENTIFY THE STRONGEST REASONING**:
   - Which model's reasoning is most rigorous?
   - If models reach different conclusions, whose logic is more sound?

4. **SYNTHESIZE**: Based on your analysis, what is the correct answer?

## Your Analysis:

**Approach Comparison:**
[Compare how different models approached the problem]

**Points of Agreement:**
[What do the models agree on?]

**Points of Disagreement:**
[Where do they differ and why?]

**Reasoning Quality Assessment:**
[Which reasoning chains are strongest/weakest?]

**Final Conclusion:**
[Your synthesized answer based on the above analysis]

CRITICAL FOR MULTIPLE CHOICE: Your FINAL line must be exactly "ANSWER: X" where X is ONLY the letter (A, B, C, or D).
Do NOT include the answer content, just the letter. Example: "ANSWER: D" NOT "ANSWER: 11" or "ANSWER: D (11 carbons)"

For non-multiple-choice questions: "ANSWER: <your final answer>"

ANSWER:"""


# Critique mode: models critique each other's answers, then revise
CRITIQUE_PROMPT = """You are reviewing another AI model's answer to this question.

## Original Question:
{question}

## The Model's Answer:
{answer}

## Your Task:
Critically evaluate this answer:

1. **ACCURACY CHECK**: Is the reasoning correct? Are there any errors in logic, calculation, or facts?
2. **COMPLETENESS**: Did the model consider all relevant factors?
3. **CONCLUSION VALIDITY**: Does the conclusion follow from the reasoning?

If you find errors or disagree, explain WHY specifically. If the answer is correct, confirm what makes it sound.

Your critique:"""


REVISION_PROMPT = """You answered a question, and other AI models have critiqued your answer.

## Original Question:
{question}

## Your Original Answer:
{original_answer}

## Critiques from Other Models:
{critiques}

## Your Task:
Consider the critiques carefully:
1. Which critiques raise valid points?
2. Which critiques are mistaken?
3. Should you revise your answer based on the feedback?

If the critiques identify genuine errors, correct your answer.
If your original answer was correct, defend it and explain why the critiques are wrong.

CRITICAL FOR MULTIPLE CHOICE: Your FINAL line must be exactly "ANSWER: X" where X is ONLY the letter (A, B, C, or D).

Your revised answer:"""


CRITIQUE_SYNTHESIS_PROMPT = """Multiple AI models answered a question, received critiques from each other, and revised their answers.

## Original Question:
{question}

## Model Answers After Revision:
{revised_answers}

## Your Task:
Synthesize the final answer based on the deliberation:

1. Which model(s) changed their answer after critique? Why?
2. Which model(s) defended their original answer? Were their defenses convincing?
3. What is the consensus (if any)?
4. Based on the quality of reasoning and responses to critique, what is the correct answer?

CRITICAL FOR MULTIPLE CHOICE: Your FINAL line must be exactly "ANSWER: X" where X is ONLY the letter (A, B, C, or D).

ANSWER:"""


# Adversarial debate mode: argue for AND against each option
DEBATE_FOR_PROMPT = """You must argue IN FAVOR of answer option {option} for this question.

## Question:
{question}

## Your Task:
Make the STRONGEST possible case for why {option} is the correct answer.
- Present evidence and reasoning supporting this option
- Explain why this answer makes sense
- Address potential objections proactively

Even if you think another answer is correct, argue convincingly for {option}.

Your argument FOR {option}:"""


DEBATE_AGAINST_PROMPT = """You must argue AGAINST answer option {option} for this question.

## Question:
{question}

## Your Task:
Make the STRONGEST possible case for why {option} is WRONG.
- Identify flaws, errors, or problems with this answer
- Present counter-evidence or counter-reasoning
- Explain what this answer gets wrong

Even if you think {option} might be correct, argue convincingly against it.

Your argument AGAINST {option}:"""


DEBATE_JUDGE_PROMPT = """You are judging a debate about a multiple choice question. Different AI models argued FOR and AGAINST each answer option.

## Question:
{question}

## Arguments FOR each option:
{arguments_for}

## Arguments AGAINST each option:
{arguments_against}

## Your Task:
Analyze the debate carefully:

1. **Strength of FOR arguments**: Which option had the most compelling supporting arguments?
2. **Strength of AGAINST arguments**: Which options had fatal flaws identified?
3. **Surviving options**: Which options survived the strongest attacks?
4. **Final verdict**: Based on the debate, which answer is correct?

Consider: A correct answer should have strong FOR arguments AND weak AGAINST arguments (the attacks should fail to identify real flaws).

CRITICAL: Your FINAL line must be exactly "ANSWER: X" where X is ONLY the letter (A, B, C, or D).

Your judgment:

ANSWER:"""


class MindsSolver(Solver):
    """Multi-model collaboration solver.

    Queries multiple AI models in parallel, applies rate limiting,
    and synthesizes responses using Claude. Supports model fallbacks
    when primary models are unavailable.

    Modes:
        - baseline: Standard multi-model synthesis (default)
        - rigor: Truth-aware prompting with epistemic calibration
        - deep: Pre-synthesis self-critique + cross-verification synthesis
        - reasoning: Explicit step-by-step reasoning with cross-model discussion
        - critique: Models critique each other's answers, then revise based on feedback
        - critique2: Two rounds of critique and revision for deeper refinement
        - debate: Adversarial debate - models argue FOR and AGAINST each option
    """

    name = "minds"

    def __init__(
        self,
        models: Optional[list[str]] = None,
        synthesizer_model: str = DEFAULT_SYNTHESIZER,
        rate_limits: Optional[dict[str, int]] = None,
        fallbacks: Optional[dict[str, list[str]]] = None,
        use_fallbacks: bool = True,
        mode: str = "baseline",
    ):
        """Initialize MindsSolver.

        Args:
            models: List of model identifiers to query
            synthesizer_model: Model to use for synthesis
            rate_limits: Custom rate limits per provider
            fallbacks: Custom model fallback mapping (model -> [fallbacks])
            use_fallbacks: Whether to use fallbacks on model errors
            mode: Solver mode - "baseline", "rigor", or "deep"
        """
        self.models = models or DEFAULT_MODELS
        self.synthesizer_model = synthesizer_model
        self.rate_limiter = RateLimiter(provider_limits=rate_limits)
        self.fallbacks = fallbacks if fallbacks is not None else DEFAULT_FALLBACKS
        self.use_fallbacks = use_fallbacks
        self.mode = mode
        self._model_cache: dict[str, Any] = {}
        self._fallback_stats: dict[str, int] = {}  # Track fallback usage

    @property
    def metadata(self) -> dict:
        """Return solver metadata for logging."""
        return {
            "name": self.name,
            "mode": self.mode,
            "models": self.models,
            "synthesizer": self.synthesizer_model,
            "model_count": len(self.models),
            "use_fallbacks": self.use_fallbacks,
            "fallback_stats": self._fallback_stats,
        }

    async def _get_model(self, model_id: str):
        """Get or create an Inspect model instance.

        Uses caching to avoid recreating models.
        """
        if model_id not in self._model_cache:
            from inspect_ai.model import get_model
            self._model_cache[model_id] = get_model(model_id)
        return self._model_cache[model_id]

    def _format_multiple_choice(self, state: Any) -> str:
        """Format multiple choice question with letter options.

        Returns formatted prompt if state has choices, otherwise returns None.
        """
        # Check if this is a multiple choice question
        choices = getattr(state, 'choices', None)
        if not choices:
            return None

        # Get the question input
        input_text = ""
        if hasattr(state, 'input'):
            input_text = str(state.input)
        elif hasattr(state, 'messages') and state.messages:
            # Extract from first user message
            for msg in state.messages:
                if hasattr(msg, 'role') and msg.role == 'user':
                    input_text = str(msg.content) if hasattr(msg, 'content') else str(msg)
                    break

        if not input_text:
            return None

        # Format with A/B/C/D options
        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        options = []
        for i, choice in enumerate(choices[:len(letters)]):
            options.append(f"{letters[i]}) {choice}")

        formatted = f"""Answer the following multiple choice question. The entire content of your response should be of the following format: 'ANSWER: $LETTER' (without quotes) where LETTER is one of {','.join(letters[:len(choices)])}.

{input_text}

{chr(10).join(options)}"""
        return formatted

    async def _query_single_model(
        self,
        model_id: str,
        state: Any,
    ) -> str:
        """Query a single model (without fallback logic).

        Args:
            model_id: Model identifier
            state: Inspect TaskState

        Returns:
            Model response text

        Raises:
            Exception: If model query fails
        """
        # Apply rate limiting
        provider = self.rate_limiter.get_provider_from_model(model_id)
        await self.rate_limiter.acquire(provider)

        # Get the model
        model = await self._get_model(model_id)

        # Check for multiple choice format
        from inspect_ai.model import ChatMessageUser, ChatMessageSystem

        mc_prompt = self._format_multiple_choice(state)

        # For reasoning mode, wrap the question with reasoning prompt
        if self.mode == "reasoning":
            if mc_prompt:
                # Add reasoning instructions to multiple choice
                reasoning_mc = REASONING_QUERY_PROMPT.format(question=mc_prompt)
                messages = [ChatMessageUser(content=reasoning_mc)]
            else:
                # Add reasoning instructions to regular question
                question = ""
                if hasattr(state, 'messages') and state.messages:
                    for msg in state.messages:
                        if hasattr(msg, 'role') and msg.role == 'user':
                            question = str(msg.content) if hasattr(msg, 'content') else str(msg)
                            break
                reasoning_q = REASONING_QUERY_PROMPT.format(question=question)
                messages = [ChatMessageUser(content=reasoning_q)]
        elif mc_prompt:
            # Use formatted multiple choice prompt
            messages = [ChatMessageUser(content=mc_prompt)]
        else:
            # Use existing messages
            messages = list(state.messages) if hasattr(state, 'messages') else []

        # Add rigor system prompt for rigor and deep modes
        if self.mode in ("rigor", "deep"):
            # Prepend system message if not already present
            if not messages or not hasattr(messages[0], 'role') or messages[0].role != 'system':
                messages.insert(0, ChatMessageSystem(content=RIGOR_SYSTEM_PROMPT))

        # Generate response
        response = await model.generate(messages)

        # Extract text from response
        if hasattr(response, 'completion'):
            return response.completion
        elif hasattr(response, 'message') and hasattr(response.message, 'content'):
            return str(response.message.content)
        return str(response)

    async def _query_model(
        self,
        model_id: str,
        state: Any,
        generate: Any
    ) -> tuple[str, str]:
        """Query a single model with rate limiting and fallback support.

        Args:
            model_id: Model identifier
            state: Inspect TaskState
            generate: Inspect generate function

        Returns:
            Tuple of (actual_model_used, response_text)
        """
        # Try primary model first
        try:
            response = await self._query_single_model(model_id, state)
            return (model_id, response)
        except Exception as primary_error:
            # If fallbacks disabled or no fallbacks configured, return error
            if not self.use_fallbacks or model_id not in self.fallbacks:
                return (model_id, f"[Error from {model_id}: {str(primary_error)[:200]}]")

            # Try fallbacks in order
            for fallback_model in self.fallbacks[model_id]:
                try:
                    response = await self._query_single_model(fallback_model, state)
                    # Track fallback usage
                    self._fallback_stats[fallback_model] = self._fallback_stats.get(fallback_model, 0) + 1
                    return (f"{fallback_model} (fallback for {model_id})", response)
                except Exception:
                    continue  # Try next fallback

            # All fallbacks failed
            return (model_id, f"[Error from {model_id} and all fallbacks: {str(primary_error)[:200]}]")

    async def _self_critique(
        self,
        model_id: str,
        original_response: str,
    ) -> str:
        """Apply self-critique to a model's response (deep mode only).

        Args:
            model_id: Model identifier
            original_response: The model's original response

        Returns:
            Critiqued/corrected response
        """
        # Apply rate limiting
        provider = self.rate_limiter.get_provider_from_model(model_id)
        await self.rate_limiter.acquire(provider)

        # Get the model
        model = await self._get_model(model_id)

        # Create critique prompt
        from inspect_ai.model import ChatMessageUser
        critique_prompt = SELF_CRITIQUE_PROMPT.format(response=original_response)

        response = await model.generate([ChatMessageUser(content=critique_prompt)])

        # Extract text from response
        if hasattr(response, 'completion'):
            return response.completion
        elif hasattr(response, 'message') and hasattr(response.message, 'content'):
            return str(response.message.content)
        return str(response)

    async def _get_critique(
        self,
        critic_model_id: str,
        question: str,
        answer_to_critique: str,
    ) -> str:
        """Have one model critique another model's answer.

        Args:
            critic_model_id: Model that will provide the critique
            question: The original question
            answer_to_critique: The answer being critiqued

        Returns:
            The critique text
        """
        # Apply rate limiting
        provider = self.rate_limiter.get_provider_from_model(critic_model_id)
        await self.rate_limiter.acquire(provider)

        # Get the model
        model = await self._get_model(critic_model_id)

        from inspect_ai.model import ChatMessageUser
        critique_prompt = CRITIQUE_PROMPT.format(
            question=question,
            answer=answer_to_critique
        )

        response = await model.generate([ChatMessageUser(content=critique_prompt)])

        if hasattr(response, 'completion'):
            return response.completion
        elif hasattr(response, 'message') and hasattr(response.message, 'content'):
            return str(response.message.content)
        return str(response)

    async def _get_revision(
        self,
        model_id: str,
        question: str,
        original_answer: str,
        critiques: list[tuple[str, str]],
    ) -> str:
        """Have a model revise its answer based on critiques.

        Args:
            model_id: The model revising its answer
            question: The original question
            original_answer: The model's original answer
            critiques: List of (critic_model_id, critique_text) tuples

        Returns:
            The revised answer
        """
        # Apply rate limiting
        provider = self.rate_limiter.get_provider_from_model(model_id)
        await self.rate_limiter.acquire(provider)

        # Get the model
        model = await self._get_model(model_id)

        # Format critiques
        formatted_critiques = "\n\n".join([
            f"### Critique from {critic_id}:\n{critique}"
            for critic_id, critique in critiques
        ])

        from inspect_ai.model import ChatMessageUser
        revision_prompt = REVISION_PROMPT.format(
            question=question,
            original_answer=original_answer,
            critiques=formatted_critiques
        )

        response = await model.generate([ChatMessageUser(content=revision_prompt)])

        if hasattr(response, 'completion'):
            return response.completion
        elif hasattr(response, 'message') and hasattr(response.message, 'content'):
            return str(response.message.content)
        return str(response)

    async def _run_critique_workflow(
        self,
        state: Any,
        initial_responses: list[tuple[str, str]],
    ) -> list[tuple[str, str]]:
        """Run the full critique workflow.

        1. Each model critiques other models' answers
        2. Each model revises based on critiques received

        Args:
            state: TaskState with the question
            initial_responses: List of (model_id, answer) tuples

        Returns:
            List of (model_id, revised_answer) tuples
        """
        # Get the question text
        question = ""
        mc_prompt = self._format_multiple_choice(state)
        if mc_prompt:
            question = mc_prompt
        elif hasattr(state, 'input'):
            question = str(state.input)
        elif hasattr(state, 'messages') and state.messages:
            for msg in state.messages:
                if hasattr(msg, 'role') and msg.role == 'user':
                    question = str(msg.content) if hasattr(msg, 'content') else str(msg)
                    break

        # Filter out error responses
        valid_responses = [(m, r) for m, r in initial_responses if not r.startswith("[Error")]

        if len(valid_responses) < 2:
            # Not enough responses to critique
            return initial_responses

        # Phase 1: Each model critiques others
        # For efficiency, each model critiques one other model (round-robin)
        all_critiques: dict[str, list[tuple[str, str]]] = {m: [] for m, _ in valid_responses}

        critique_tasks = []
        for i, (model_id, answer) in enumerate(valid_responses):
            # Get critique from next model in list (round-robin)
            critic_idx = (i + 1) % len(valid_responses)
            critic_model = valid_responses[critic_idx][0]

            async def get_critique_task(critic=critic_model, q=question, a=answer, target=model_id):
                critique = await self._get_critique(critic, q, a)
                return (target, critic, critique)

            critique_tasks.append(get_critique_task())

        # Run critiques in parallel
        critique_results = await asyncio.gather(*critique_tasks, return_exceptions=True)

        for result in critique_results:
            if isinstance(result, Exception):
                continue
            target_model, critic_model, critique = result
            all_critiques[target_model].append((critic_model, critique))

        # Phase 2: Each model revises based on critiques
        revision_tasks = []
        for model_id, original_answer in valid_responses:
            critiques = all_critiques.get(model_id, [])
            if critiques:
                async def get_revision_task(m=model_id, q=question, a=original_answer, c=critiques):
                    revised = await self._get_revision(m, q, a, c)
                    return (m, revised)
                revision_tasks.append(get_revision_task())
            else:
                # No critiques, keep original
                async def keep_original(m=model_id, a=original_answer):
                    return (m, a)
                revision_tasks.append(keep_original())

        # Run revisions in parallel
        revision_results = await asyncio.gather(*revision_tasks, return_exceptions=True)

        revised_responses = []
        for i, result in enumerate(revision_results):
            if isinstance(result, Exception):
                revised_responses.append(valid_responses[i])
            else:
                revised_responses.append(result)

        return revised_responses

    async def _run_debate_workflow(
        self,
        state: Any,
    ) -> tuple[str, str]:
        """Run adversarial debate: models argue FOR and AGAINST each option.

        Args:
            state: TaskState with the question and choices

        Returns:
            Tuple of (arguments_for, arguments_against) formatted strings
        """
        # Get the question and choices
        mc_prompt = self._format_multiple_choice(state)
        if not mc_prompt:
            return ("", "")

        choices = getattr(state, 'choices', [])
        if not choices:
            return ("", "")

        letters = ['A', 'B', 'C', 'D'][:len(choices)]

        # Use first 2-3 models for debate (to manage cost)
        debate_models = self.models[:min(3, len(self.models))]

        # Phase 1: Collect FOR arguments for each option
        for_tasks = []
        for i, letter in enumerate(letters):
            model_idx = i % len(debate_models)
            model_id = debate_models[model_idx]

            async def get_for_arg(m=model_id, opt=letter, q=mc_prompt):
                provider = self.rate_limiter.get_provider_from_model(m)
                await self.rate_limiter.acquire(provider)
                model = await self._get_model(m)
                from inspect_ai.model import ChatMessageUser
                prompt = DEBATE_FOR_PROMPT.format(option=opt, question=q)
                response = await model.generate([ChatMessageUser(content=prompt)])
                text = response.completion if hasattr(response, 'completion') else str(response.message.content)
                return (opt, m, text)

            for_tasks.append(get_for_arg())

        # Phase 2: Collect AGAINST arguments for each option
        against_tasks = []
        for i, letter in enumerate(letters):
            # Use different model than the one arguing FOR
            model_idx = (i + 1) % len(debate_models)
            model_id = debate_models[model_idx]

            async def get_against_arg(m=model_id, opt=letter, q=mc_prompt):
                provider = self.rate_limiter.get_provider_from_model(m)
                await self.rate_limiter.acquire(provider)
                model = await self._get_model(m)
                from inspect_ai.model import ChatMessageUser
                prompt = DEBATE_AGAINST_PROMPT.format(option=opt, question=q)
                response = await model.generate([ChatMessageUser(content=prompt)])
                text = response.completion if hasattr(response, 'completion') else str(response.message.content)
                return (opt, m, text)

            against_tasks.append(get_against_arg())

        # Run all debates in parallel
        all_results = await asyncio.gather(*for_tasks, *against_tasks, return_exceptions=True)

        # Split results
        for_results = all_results[:len(letters)]
        against_results = all_results[len(letters):]

        # Format FOR arguments
        for_args = []
        for result in for_results:
            if isinstance(result, Exception):
                continue
            opt, model, text = result
            for_args.append(f"### Option {opt} (argued by {model}):\n{text}")
        arguments_for = "\n\n".join(for_args)

        # Format AGAINST arguments
        against_args = []
        for result in against_results:
            if isinstance(result, Exception):
                continue
            opt, model, text = result
            against_args.append(f"### Against Option {opt} (argued by {model}):\n{text}")
        arguments_against = "\n\n".join(against_args)

        return (arguments_for, arguments_against)

    async def _synthesize(
        self,
        state: Any,
        responses: list[tuple[str, str]],
        generate: Any
    ) -> Any:
        """Synthesize responses from all models.

        Args:
            state: Original TaskState
            responses: List of (model_id, response_text) tuples
            generate: Inspect generate function

        Returns:
            Updated TaskState with synthesized answer
        """
        # For deep mode, apply self-critique to each response first
        if self.mode == "deep":
            critiqued_responses = []
            for model_id, response in responses:
                if not response.startswith("[Error"):
                    critiqued = await self._self_critique(model_id, response)
                    critiqued_responses.append((model_id, critiqued))
                else:
                    critiqued_responses.append((model_id, response))
            responses = critiqued_responses

        # For critique mode, run the full critique-revision workflow
        if self.mode == "critique":
            responses = await self._run_critique_workflow(state, responses)

        # For critique2 mode, run TWO rounds of critique-revision
        if self.mode == "critique2":
            responses = await self._run_critique_workflow(state, responses)
            # Second round
            responses = await self._run_critique_workflow(state, responses)

        # For debate mode, run adversarial debate instead of using initial responses
        debate_for = ""
        debate_against = ""
        if self.mode == "debate":
            debate_for, debate_against = await self._run_debate_workflow(state)

        # Format responses for synthesis
        formatted_responses = "\n\n".join([
            f"### {model_id}\n{response}"
            for model_id, response in responses
        ])

        # Get question for critique/debate synthesis prompt
        question = ""
        if self.mode in ("critique", "critique2", "debate"):
            mc_prompt = self._format_multiple_choice(state)
            if mc_prompt:
                question = mc_prompt
            elif hasattr(state, 'input'):
                question = str(state.input)

        # Use appropriate synthesis prompt based on mode
        if self.mode == "deep":
            synthesis_prompt = DEEP_SYNTHESIS_PROMPT.format(responses=formatted_responses)
        elif self.mode == "reasoning":
            synthesis_prompt = REASONING_SYNTHESIS_PROMPT.format(responses=formatted_responses)
        elif self.mode in ("critique", "critique2"):
            synthesis_prompt = CRITIQUE_SYNTHESIS_PROMPT.format(
                question=question,
                revised_answers=formatted_responses
            )
        elif self.mode == "debate":
            synthesis_prompt = DEBATE_JUDGE_PROMPT.format(
                question=question,
                arguments_for=debate_for,
                arguments_against=debate_against
            )
        else:
            synthesis_prompt = SYNTHESIS_PROMPT.format(responses=formatted_responses)

        # Apply rate limiting for synthesizer
        provider = self.rate_limiter.get_provider_from_model(self.synthesizer_model)
        await self.rate_limiter.acquire(provider)

        # Use the main generate function with synthesizer model
        # Create a modified state with the synthesis prompt
        from copy import deepcopy
        synth_state = deepcopy(state)

        # Add synthesis prompt to messages
        if hasattr(synth_state, 'messages'):
            from inspect_ai.model import ChatMessageUser
            synth_state.messages.append(ChatMessageUser(content=synthesis_prompt))

        # Generate synthesized response
        return await generate(synth_state)

    def _extract_answer_letter(self, text: str) -> str | None:
        """Extract answer letter from ANSWER: X format."""
        import re
        # Look for ANSWER: followed by a single letter (A-H), ignoring markdown formatting
        # Pattern handles: "ANSWER: C", "ANSWER: C**", "ANSWER: **C**", etc.
        match = re.search(r'ANSWER:\s*\*{0,2}([A-Ha-h])\b', text)
        if match:
            return match.group(1).upper()
        return None

    def _set_choice_correct(self, state: Any, answer_letter: str) -> None:
        """Set the correct choice based on the extracted answer letter."""
        if not hasattr(state, 'choices') or not state.choices:
            return

        # Map letter to index
        letter_to_index = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7}
        selected_index = letter_to_index.get(answer_letter)

        if selected_index is None:
            return

        # Set the correct attribute on choices
        for i, choice in enumerate(state.choices):
            choice.correct = (i == selected_index)

    async def solve(self, state: Any, generate: Any) -> Any:
        """Generate solution using multi-model collaboration.

        Args:
            state: Inspect TaskState with input, messages, tools
            generate: Inspect generate function

        Returns:
            Updated TaskState with synthesized solution
        """
        # Query all models in parallel
        tasks = [
            self._query_model(model_id, state, generate)
            for model_id in self.models
        ]

        # Wait for all responses (with error handling)
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results - _query_model now returns (model_label, response_text)
        response_pairs = []
        for model_id, result in zip(self.models, results):
            if isinstance(result, Exception):
                response_pairs.append((model_id, f"[Error: {str(result)[:200]}]"))
            else:
                # result is (actual_model_label, response_text)
                response_pairs.append(result)

        # Synthesize responses
        result_state = await self._synthesize(state, response_pairs, generate)

        # For multiple choice: extract answer and set choice.correct
        if hasattr(result_state, 'output') and result_state.output:
            output_text = getattr(result_state.output, 'completion', str(result_state.output))
            answer_letter = self._extract_answer_letter(output_text)
            if answer_letter:
                self._set_choice_correct(result_state, answer_letter)

        return result_state
