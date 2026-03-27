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

Import agents directly from their subpackages:
    from AGENT.ontology_generator import OntologyGenerator
    from AGENT.report_agent import ReportAgent
    from AGENT.oasis_profile_generator import OasisProfileGenerator
    from AGENT.simulation_config_generator import SimulationConfigGenerator

Non-agent utilities and infrastructure live in backend/app/services/.
"""
