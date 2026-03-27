"""
AGENT - Universal Swarm Intelligence Engine
D.E.E.P.A.K. - Distributed Environment for Extrapolating Probability and Artificial Knowledge

This directory contains only autonomous swarm agents — modules that use LLM
reasoning, make autonomous decisions, and generate content.

Swarm Agents:
-------------
- ontology_generator/          : LLM-powered domain ontology design agent
- simulation_config_generator/ : LLM-powered simulation parameter generation agent
- report_agent/                : Multi-step ReACT reasoning agent with tool use
- oasis_profile_generator/     : LLM-powered agent profile generation

Non-agent utilities and infrastructure live in backend/app/services/.
"""

from .ontology_generator import *
from .simulation_config_generator import *
from .report_agent import *
from .oasis_profile_generator import *
