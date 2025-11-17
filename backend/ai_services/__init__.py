"""
AI Services Package

Centralized AI services using Anthropic Claude:

Validators:
- content_validator: Validates learning content for accuracy and consistency

Evaluators:
- ai_answer_evaluator: Evaluates user's written answers
- ai_title_evaluator: Evaluates user's guessed titles

Generators:
- mc_generator: Generates multiple choice options
- ai_question_generator: Generates weekly test questions (LangChain + LangGraph)

Graphs (LangGraph Workflows):
- generate_quality_choices: High-quality distractor generation
- select_balanced_contents_for_test: Balanced test content selection
"""

__version__ = "2.0.0"

from .evaluators import ai_answer_evaluator, ai_title_evaluator
from .generators import (
    ai_question_generator, generate_multiple_choice_options, mc_generator,
)
from .graphs import (
    create_distractor_generation_graph, create_weekly_test_balance_graph,
    generate_quality_choices, select_balanced_contents_for_test,
)
# Import all services for easy access
from .validators import content_validator, validate_content

__all__ = [
    # Validators
    'content_validator',
    'validate_content',

    # Evaluators
    'ai_answer_evaluator',
    'ai_title_evaluator',

    # Generators
    'mc_generator',
    'generate_multiple_choice_options',
    'ai_question_generator',

    # Graphs
    'generate_quality_choices',
    'select_balanced_contents_for_test',
    'create_distractor_generation_graph',
    'create_weekly_test_balance_graph',
]
