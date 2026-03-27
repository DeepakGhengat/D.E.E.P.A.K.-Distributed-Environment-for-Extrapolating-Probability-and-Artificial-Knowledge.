"""
Business Service Module

All swarm agents are organized in the AGENT/ directory at the project root.
This module re-exports them for backward compatibility with existing backend code.
"""

import sys
import os

# Add project root to path so AGENT package is importable
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from AGENT.ontology_generator import OntologyGenerator
from AGENT.graph_builder import GraphBuilderService
from AGENT.text_processor import TextProcessor
from AGENT.zep_entity_reader import ZepEntityReader, EntityNode, FilteredEntities
from AGENT.oasis_profile_generator import OasisProfileGenerator, OasisAgentProfile
from AGENT.simulation_manager import SimulationManager, SimulationState, SimulationStatus
from AGENT.simulation_config_generator import (
    SimulationConfigGenerator,
    SimulationParameters,
    AgentActivityConfig,
    TimeSimulationConfig,
    EventConfig,
    PlatformConfig
)
from AGENT.simulation_runner import (
    SimulationRunner,
    SimulationRunState,
    RunnerStatus,
    AgentAction,
    RoundSummary
)
from AGENT.zep_graph_memory_updater import (
    ZepGraphMemoryUpdater,
    ZepGraphMemoryManager,
    AgentActivity
)
from AGENT.simulation_ipc import (
    SimulationIPCClient,
    SimulationIPCServer,
    IPCCommand,
    IPCResponse,
    CommandType,
    CommandStatus
)

__all__ = [
    'OntologyGenerator',
    'GraphBuilderService',
    'TextProcessor',
    'ZepEntityReader',
    'EntityNode',
    'FilteredEntities',
    'OasisProfileGenerator',
    'OasisAgentProfile',
    'SimulationManager',
    'SimulationState',
    'SimulationStatus',
    'SimulationConfigGenerator',
    'SimulationParameters',
    'AgentActivityConfig',
    'TimeSimulationConfig',
    'EventConfig',
    'PlatformConfig',
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
