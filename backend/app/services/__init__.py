"""
Business Service Module

Agents (LLM-powered autonomous reasoning) live in the AGENT/ directory.
Utilities and infrastructure services live here in backend/app/services/.
"""

import sys
import os

# Add project root to path so AGENT package is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# --- Agents (from AGENT/ directory) ---
from AGENT.ontology_generator import OntologyGenerator
from AGENT.report_agent import *
from AGENT.oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from AGENT.simulation_config_generator import (
    SimulationConfigGenerator,
    SimulationParameters,
    AgentActivityConfig,
    TimeSimulationConfig,
    EventConfig,
    PlatformConfig
)

# --- Utilities & Infrastructure (local services) ---
from .graph_builder import GraphBuilderService
from .text_processor import TextProcessor
from .zep_entity_reader import ZepEntityReader, EntityNode, FilteredEntities
from .simulation_manager import SimulationManager, SimulationState, SimulationStatus
from .simulation_runner import (
    SimulationRunner,
    SimulationRunState,
    RunnerStatus,
    AgentAction,
    RoundSummary
)
from .zep_graph_memory_updater import (
    ZepGraphMemoryUpdater,
    ZepGraphMemoryManager,
    AgentActivity
)
from .simulation_ipc import (
    SimulationIPCClient,
    SimulationIPCServer,
    IPCCommand,
    IPCResponse,
    CommandType,
    CommandStatus
)

__all__ = [
    # Agents
    'OntologyGenerator',
    'OasisProfileGenerator',
    'OasisAgentProfile',
    'SimulationConfigGenerator',
    'SimulationParameters',
    'AgentActivityConfig',
    'TimeSimulationConfig',
    'EventConfig',
    'PlatformConfig',
    # Utilities & Infrastructure
    'GraphBuilderService',
    'TextProcessor',
    'ZepEntityReader',
    'EntityNode',
    'FilteredEntities',
    'SimulationManager',
    'SimulationState',
    'SimulationStatus',
    'SimulationRunner',
    'SimulationRunState',
    'RunnerStatus',
    'AgentAction',
    'RoundSummary',
    'ZepGraphMemoryUpdater',
    'ZepGraphMemoryManager',
    'AgentActivity',
    'SimulationIPCClient',
    'SimulationIPCServer',
    'IPCCommand',
    'IPCResponse',
    'CommandType',
    'CommandStatus',
]
