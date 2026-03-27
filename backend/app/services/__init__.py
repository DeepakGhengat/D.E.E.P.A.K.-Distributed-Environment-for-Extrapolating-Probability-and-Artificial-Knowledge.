"""
Business Service Module

Agents (LLM-powered autonomous reasoning) live in the AGENT/ directory.
Utilities and infrastructure services live here in backend/app/services/.

Import agents directly from AGENT package:
    from AGENT.ontology_generator import OntologyGenerator
    from AGENT.report_agent import ReportAgent
    from AGENT.oasis_profile_generator import OasisProfileGenerator
    from AGENT.simulation_config_generator import SimulationConfigGenerator
"""

import sys
import os

# Add project root to path so AGENT package is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# --- Utilities & Infrastructure (local services only) ---
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
