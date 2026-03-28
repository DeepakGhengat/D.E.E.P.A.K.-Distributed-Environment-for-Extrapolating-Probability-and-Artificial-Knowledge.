"""
OASISSimulation runner
inafterplatformRunSimulatedand records EachAgent's actions, SupportsReal-timestatusMonitor
"""

import os
import sys
import json
import time
import asyncio
import threading
import subprocess
import signal
import atexit
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from queue import Queue

from ..config import Config
from ..utils.logger import get_logger
from .zep_graph_memory_updater import ZepGraphMemoryManager
from .simulation_ipc import SimulationIPCClient, CommandType, IPCResponse

logger = get_logger('deepak.simulation_runner')

# MarkiswhetheralreadyRegisterClean upFunction
_cleanup_registered = False

# Platformdetect
IS_WINDOWS = sys.platform == 'win32'


class RunnerStatus(str, Enum):
    """Runner status"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentAction:
    """AgentAction record"""
    round_num: int
    timestamp: str
    platform: str  # twitter / reddit
    agent_id: int
    agent_name: str
    action_type: str  # CREATE_POST, LIKE_POST, etc.
    action_args: Dict[str, Any] = field(default_factory=dict)
    result: Optional[str] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "timestamp": self.timestamp,
            "platform": self.platform,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "action_type": self.action_type,
            "action_args": self.action_args,
            "result": self.result,
            "success": self.success,
        }


@dataclass
class RoundSummary:
    """per-roundSummary"""
    round_num: int
    start_time: str
    end_time: Optional[str] = None
    simulated_hour: int = 0
    twitter_actions: int = 0
    reddit_actions: int = 0
    active_agents: List[int] = field(default_factory=list)
    actions: List[AgentAction] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "round_num": self.round_num,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "simulated_hour": self.simulated_hour,
            "twitter_actions": self.twitter_actions,
            "reddit_actions": self.reddit_actions,
            "active_agents": self.active_agents,
            "actions_count": len(self.actions),
            "actions": [a.to_dict() for a in self.actions],
        }


@dataclass
class SimulationRunState:
    """Simulation run state(Real-time)"""
    simulation_id: str
    runner_status: RunnerStatus = RunnerStatus.IDLE
    
    # Progress information
    current_round: int = 0
    total_rounds: int = 0
    simulated_hours: int = 0
    total_simulation_hours: int = 0
    
    # per-PlatformIndependentRound and SimulatedTime(foratDualPlatformParallelDisplay)
    twitter_current_round: int = 0
    reddit_current_round: int = 0
    twitter_simulated_hours: int = 0
    reddit_simulated_hours: int = 0
    
    # Platformstatus
    twitter_running: bool = False
    reddit_running: bool = False
    twitter_actions_count: int = 0
    reddit_actions_count: int = 0
    
    # PlatformCompletedstatus (via detection of actions.jsonl in's  simulation_end  events)
    twitter_completed: bool = False
    reddit_completed: bool = False
    
    # per-roundSummary
    rounds: List[RoundSummary] = field(default_factory=list)
    
    # recent actions(Used by frontendReal-timeShow)
    recent_actions: List[AgentAction] = field(default_factory=list)
    max_recent_actions: int = 50
    
    # Timestamp
    started_at: Optional[str] = None
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    # Error information
    error: Optional[str] = None
    
    # ProcessID(foratStop)
    process_pid: Optional[int] = None
    
    def add_action(self, action: AgentAction):
        """Add action torecent Action list"""
        self.recent_actions.insert(0, action)
        if len(self.recent_actions) > self.max_recent_actions:
            self.recent_actions = self.recent_actions[:self.max_recent_actions]
        
        if action.platform == "twitter":
            self.twitter_actions_count += 1
        else:
            self.reddit_actions_count += 1
        
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "runner_status": self.runner_status.value,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "simulated_hours": self.simulated_hours,
            "total_simulation_hours": self.total_simulation_hours,
            "progress_percent": round(self.current_round / max(self.total_rounds, 1) * 100, 1),
            # per-PlatformIndependentRound and Time
            "twitter_current_round": self.twitter_current_round,
            "reddit_current_round": self.reddit_current_round,
            "twitter_simulated_hours": self.twitter_simulated_hours,
            "reddit_simulated_hours": self.reddit_simulated_hours,
            "twitter_running": self.twitter_running,
            "reddit_running": self.reddit_running,
            "twitter_completed": self.twitter_completed,
            "reddit_completed": self.reddit_completed,
            "twitter_actions_count": self.twitter_actions_count,
            "reddit_actions_count": self.reddit_actions_count,
            "total_actions_count": self.twitter_actions_count + self.reddit_actions_count,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "process_pid": self.process_pid,
        }
    
    def to_detail_dict(self) -> Dict[str, Any]:
        """Containsrecent actions's Detailed information"""
        result = self.to_dict()
        result["recent_actions"] = [a.to_dict() for a in self.recent_actions]
        result["rounds_count"] = len(self.rounds)
        return result


class SimulationRunner:
    """
    Simulation runner
    
    Responsible for:
    1. inBackground processinRunOASISSimulated
    2. ParseRun logs, recordingEachAgent's actions
    3. provides Real-timestatusQueryAPI
    4. SupportsPause/stop/resumeoperations
    """
    
    # Run statestoreDirectory
    RUN_STATE_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../uploads/simulations'
    )
    
    # Script directory
    SCRIPTS_DIR = os.path.join(
        os.path.dirname(__file__),
        '../../scripts'
    )
    
    # withinexistin's Run state
    _run_states: Dict[str, SimulationRunState] = {}
    _processes: Dict[str, subprocess.Popen] = {}
    _action_queues: Dict[str, Queue] = {}
    _monitor_threads: Dict[str, threading.Thread] = {}
    _stdout_files: Dict[str, Any] = {}  # store stdout File handles
    _stderr_files: Dict[str, Any] = {}  # store stderr File handles
    
    # Graph memory updateConfiguration
    _graph_memory_enabled: Dict[str, bool] = {}  # simulation_id -> enabled
    
    @classmethod
    def get_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """GetRun state"""
        if simulation_id in cls._run_states:
            return cls._run_states[simulation_id]
        
        # try tofromFileLoad
        state = cls._load_run_state(simulation_id)
        if state:
            cls._run_states[simulation_id] = state
        return state
    
    @classmethod
    def _load_run_state(cls, simulation_id: str) -> Optional[SimulationRunState]:
        """fromFileLoadRun state"""
        state_file = os.path.join(cls.RUN_STATE_DIR, simulation_id, "run_state.json")
        if not os.path.exists(state_file):
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            state = SimulationRunState(
                simulation_id=simulation_id,
                runner_status=RunnerStatus(data.get("runner_status", "idle")),
                current_round=data.get("current_round", 0),
                total_rounds=data.get("total_rounds", 0),
                simulated_hours=data.get("simulated_hours", 0),
                total_simulation_hours=data.get("total_simulation_hours", 0),
                # per-PlatformIndependentRound and Time
                twitter_current_round=data.get("twitter_current_round", 0),
                reddit_current_round=data.get("reddit_current_round", 0),
                twitter_simulated_hours=data.get("twitter_simulated_hours", 0),
                reddit_simulated_hours=data.get("reddit_simulated_hours", 0),
                twitter_running=data.get("twitter_running", False),
                reddit_running=data.get("reddit_running", False),
                twitter_completed=data.get("twitter_completed", False),
                reddit_completed=data.get("reddit_completed", False),
                twitter_actions_count=data.get("twitter_actions_count", 0),
                reddit_actions_count=data.get("reddit_actions_count", 0),
                started_at=data.get("started_at"),
                updated_at=data.get("updated_at", datetime.now().isoformat()),
                completed_at=data.get("completed_at"),
                error=data.get("error"),
                process_pid=data.get("process_pid"),
            )
            
            # Loadrecent actions
            actions_data = data.get("recent_actions", [])
            for a in actions_data:
                state.recent_actions.append(AgentAction(
                    round_num=a.get("round_num", 0),
                    timestamp=a.get("timestamp", ""),
                    platform=a.get("platform", ""),
                    agent_id=a.get("agent_id", 0),
                    agent_name=a.get("agent_name", ""),
                    action_type=a.get("action_type", ""),
                    action_args=a.get("action_args", {}),
                    result=a.get("result"),
                    success=a.get("success", True),
                ))
            
            return state
        except Exception as e:
            logger.error(f"LoadRun stateFailed: {str(e)}")
            return None
    
    @classmethod
    def _save_run_state(cls, state: SimulationRunState):
        """SaveRun statetoFile"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        os.makedirs(sim_dir, exist_ok=True)
        state_file = os.path.join(sim_dir, "run_state.json")
        
        data = state.to_detail_dict()
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cls._run_states[state.simulation_id] = state
    
    @classmethod
    def start_simulation(
        cls,
        simulation_id: str,
        platform: str = "parallel",  # twitter / reddit / parallel
        max_rounds: int = None,  # MaxSimulatedrounds (optional, forattruncate long's Simulated)
        enable_graph_memory_update: bool = False,  # iswhetherwillActivityUpdatetoZepGraph
        graph_id: str = None  # ZepGraphID(forGraphUpdate)
    ) -> SimulationRunState:
        """
        StartSimulated
        
        Args:
            simulation_id: SimulatedID
            platform: RunPlatform (twitter/reddit/parallel)
            max_rounds: MaxSimulatedrounds (optional, forattruncate long's Simulated)
            enable_graph_memory_update: iswhetherwillAgentActivityUpdatetoZepGraph
            graph_id: ZepGraphID(forGraphUpdate)
            
        Returns:
            SimulationRunState
        """
        # CheckiswhetheralreadyinRun
        existing = cls.get_run_state(simulation_id)
        if existing and existing.runner_status in [RunnerStatus.RUNNING, RunnerStatus.STARTING]:
            raise ValueError(f"SimulatedalreadyinRunin: {simulation_id}")
        
        # LoadSimulation configuration
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        config_path = os.path.join(sim_dir, "simulation_config.json")
        
        if not os.path.exists(config_path):
            raise ValueError(f"Simulation configuration not found, please call /prepare first")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # InitializeRun state
        time_config = config.get("time_config", {})
        total_hours = time_config.get("total_simulation_hours", 72)
        minutes_per_round = time_config.get("minutes_per_round", 30)
        total_rounds = int(total_hours * 60 / minutes_per_round)
        
        # such asSpecifiedMax, thentruncate
        if max_rounds is not None and max_rounds > 0:
            original_rounds = total_rounds
            total_rounds = min(total_rounds, max_rounds)
            if total_rounds < original_rounds:
                logger.info(f"alreadytruncate: {original_rounds} -> {total_rounds} (max_rounds={max_rounds})")
        
        state = SimulationRunState(
            simulation_id=simulation_id,
            runner_status=RunnerStatus.STARTING,
            total_rounds=total_rounds,
            total_simulation_hours=total_hours,
            started_at=datetime.now().isoformat(),
        )
        
        cls._save_run_state(state)
        
        # such asforGraph memory update, CreateUpdate
        if enable_graph_memory_update:
            if not graph_id:
                raise ValueError("forGraph memory updateMustprovides  graph_id")
            
            try:
                ZepGraphMemoryManager.create_updater(simulation_id, graph_id)
                cls._graph_memory_enabled[simulation_id] = True
                logger.info(f"alreadyforGraph memory update: simulation_id={simulation_id}, graph_id={graph_id}")
            except Exception as e:
                logger.error(f"CreateGraph memory updaterFailed: {e}")
                cls._graph_memory_enabled[simulation_id] = False
        else:
            cls._graph_memory_enabled[simulation_id] = False
        
        # DetermineRunScript(Scriptat backend/scripts/ Directory)
        if platform == "twitter":
            script_name = "run_twitter_simulation.py"
            state.twitter_running = True
        elif platform == "reddit":
            script_name = "run_reddit_simulation.py"
            state.reddit_running = True
        else:
            script_name = "run_parallel_simulation.py"
            state.twitter_running = True
            state.reddit_running = True
        
        script_path = os.path.join(cls.SCRIPTS_DIR, script_name)
        
        if not os.path.exists(script_path):
            raise ValueError(f"ScriptnotExists: {script_path}")
        
        # CreateactionsQueue
        action_queue = Queue()
        cls._action_queues[simulation_id] = action_queue
        
        # Start simulationProcess
        try:
            # BuildRunCommand, UsesPath
            # NewLog structure: 
            #   twitter/actions.jsonl - Twitter Action log
            #   reddit/actions.jsonl  - Reddit Action log
            #   simulation.log        - ProcessLog
            
            cmd = [
                sys.executable,  # Python
                script_path,
                "--config", config_path,  # UsesConfigurationFile path
            ]
            
            # such asSpecifiedMax, toCommandParameters
            if max_rounds is not None and max_rounds > 0:
                cmd.extend(["--max-rounds", str(max_rounds)])
            
            # CreateLog file, avoid stdout/stderr BufferProcess
            main_log_path = os.path.join(sim_dir, "simulation.log")
            main_log_file = open(main_log_path, 'w', encoding='utf-8')
            
            # SetChild processesEnvironment variables, Ensure Windows onUses UTF-8 Encoding
            # thisCan(such as OASIS)ReadFilenotSpecifiedEncoding's Question
            env = os.environ.copy()
            env['PYTHONUTF8'] = '1'  # Python 3.7+ Supports, letAll open() DefaultUses UTF-8
            env['PYTHONIOENCODING'] = 'utf-8'  # Ensure stdout/stderr Uses UTF-8
            
            # SetWorking directoryasSimulatedDirectory(Databaseetc.FilewillGeneratein)
            # Uses start_new_session=True CreateNewProcess group, EnsureCan os.killpg TerminateAllChild processes
            process = subprocess.Popen(
                cmd,
                cwd=sim_dir,
                stdout=main_log_file,
                stderr=subprocess.STDOUT,  # stderr alsoWriteFile
                text=True,
                encoding='utf-8',  # SpecifiedEncoding
                bufsize=1,
                env=env,  # have UTF-8 Set's Environment variables
                start_new_session=True,  # CreateProcess group, EnsureServerClosecanTerminateAllProcess
            )
            
            # SaveFile handleswithafterClose
            cls._stdout_files[simulation_id] = main_log_file
            cls._stderr_files[simulation_id] = None  # notthenNeed's  stderr
            
            state.process_pid = process.pid
            state.runner_status = RunnerStatus.RUNNING
            cls._processes[simulation_id] = process
            cls._save_run_state(state)
            
            # StartMonitorThread
            monitor_thread = threading.Thread(
                target=cls._monitor_simulation,
                args=(simulation_id,),
                daemon=True
            )
            monitor_thread.start()
            cls._monitor_threads[simulation_id] = monitor_thread
            
            logger.info(f"SimulatedStartSuccessfully: {simulation_id}, pid={process.pid}, platform={platform}")
            
        except Exception as e:
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)
            raise
        
        return state
    
    @classmethod
    def _monitor_simulation(cls, simulation_id: str):
        """MonitorSimulation process, ParseAction log"""
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        # NewLog structure: Platform's Action log
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        process = cls._processes.get(simulation_id)
        state = cls.get_run_state(simulation_id)
        
        if not process or not state:
            return
        
        twitter_position = 0
        reddit_position = 0
        
        try:
            while process.poll() is None:  # ProcessinRun
                # Read Twitter Action log
                if os.path.exists(twitter_actions_log):
                    twitter_position = cls._read_action_log(
                        twitter_actions_log, twitter_position, state, "twitter"
                    )
                
                # Read Reddit Action log
                if os.path.exists(reddit_actions_log):
                    reddit_position = cls._read_action_log(
                        reddit_actions_log, reddit_position, state, "reddit"
                    )
                
                # Updatestatus
                cls._save_run_state(state)
                time.sleep(2)
            
            # ProcessEndafter, afterReadtimesLog
            if os.path.exists(twitter_actions_log):
                cls._read_action_log(twitter_actions_log, twitter_position, state, "twitter")
            if os.path.exists(reddit_actions_log):
                cls._read_action_log(reddit_actions_log, reddit_position, state, "reddit")
            
            # ProcessEnd
            exit_code = process.returncode
            
            if exit_code == 0:
                state.runner_status = RunnerStatus.COMPLETED
                state.completed_at = datetime.now().isoformat()
                logger.info(f"SimulatedCompleted: {simulation_id}")
            else:
                state.runner_status = RunnerStatus.FAILED
                # fromLog fileReadError information
                main_log_path = os.path.join(sim_dir, "simulation.log")
                error_info = ""
                try:
                    if os.path.exists(main_log_path):
                        with open(main_log_path, 'r', encoding='utf-8') as f:
                            error_info = f.read()[-2000:]  # after2000
                except Exception:
                    pass
                state.error = f"ProcessExit: {exit_code}, : {error_info}"
                logger.error(f"SimulatedFailed: {simulation_id}, error={state.error}")
            
            state.twitter_running = False
            state.reddit_running = False
            cls._save_run_state(state)
            
        except Exception as e:
            logger.error(f"MonitorThread: {simulation_id}, error={str(e)}")
            state.runner_status = RunnerStatus.FAILED
            state.error = str(e)
            cls._save_run_state(state)
        
        finally:
            # StopGraph memory updater
            if cls._graph_memory_enabled.get(simulation_id, False):
                try:
                    ZepGraphMemoryManager.stop_updater(simulation_id)
                    logger.info(f"alreadyStopGraph memory update: simulation_id={simulation_id}")
                except Exception as e:
                    logger.error(f"StopGraph memory updaterFailed: {e}")
                cls._graph_memory_enabled.pop(simulation_id, None)
            
            # Clean upProcess
            cls._processes.pop(simulation_id, None)
            cls._action_queues.pop(simulation_id, None)
            
            # CloseLogFile handles
            if simulation_id in cls._stdout_files:
                try:
                    cls._stdout_files[simulation_id].close()
                except Exception:
                    pass
                cls._stdout_files.pop(simulation_id, None)
            if simulation_id in cls._stderr_files and cls._stderr_files[simulation_id]:
                try:
                    cls._stderr_files[simulation_id].close()
                except Exception:
                    pass
                cls._stderr_files.pop(simulation_id, None)
    
    @classmethod
    def _read_action_log(
        cls, 
        log_path: str, 
        position: int, 
        state: SimulationRunState,
        platform: str
    ) -> int:
        """
        ReadactionsLog file
        
        Args:
            log_path: LogFile path
            position: ontimesRead
            state: Run stateObject
            platform: PlatformName (twitter/reddit)
            
        Returns:
            NewRead
        """
        # CheckiswhetherforGraph memory update
        graph_memory_enabled = cls._graph_memory_enabled.get(state.simulation_id, False)
        graph_updater = None
        if graph_memory_enabled:
            graph_updater = ZepGraphMemoryManager.get_updater(state.simulation_id)
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                f.seek(position)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            action_data = json.loads(line)
                            
                            # ProcessType's 
                            if "event_type" in action_data:
                                event_type = action_data.get("event_type")
                                
                                # detect simulation_end , MarkPlatformCompleted
                                if event_type == "simulation_end":
                                    if platform == "twitter":
                                        state.twitter_completed = True
                                        state.twitter_running = False
                                        logger.info(f"Twitter SimulatedCompleted: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    elif platform == "reddit":
                                        state.reddit_completed = True
                                        state.reddit_running = False
                                        logger.info(f"Reddit SimulatedCompleted: {state.simulation_id}, total_rounds={action_data.get('total_rounds')}, total_actions={action_data.get('total_actions')}")
                                    
                                    # CheckiswhetherAllfor's PlatformallCompleted
                                    # such asRunPlatform, CheckPlatform
                                    # such asRunPlatform, NeedallCompleted
                                    all_completed = cls._check_all_platforms_completed(state)
                                    if all_completed:
                                        state.runner_status = RunnerStatus.COMPLETED
                                        state.completed_at = datetime.now().isoformat()
                                        logger.info(f"AllPlatformSimulatedCompleted: {state.simulation_id}")
                                
                                # UpdateRoundInformation(from round_end  events)
                                elif event_type == "round_end":
                                    round_num = action_data.get("round", 0)
                                    simulated_hours = action_data.get("simulated_hours", 0)
                                    
                                    # Updateper-PlatformIndependent's Round and Time
                                    if platform == "twitter":
                                        if round_num > state.twitter_current_round:
                                            state.twitter_current_round = round_num
                                        state.twitter_simulated_hours = simulated_hours
                                    elif platform == "reddit":
                                        if round_num > state.reddit_current_round:
                                            state.reddit_current_round = round_num
                                        state.reddit_simulated_hours = simulated_hours
                                    
                                    # RoundPlatform's Maxvalue
                                    if round_num > state.current_round:
                                        state.current_round = round_num
                                    # TimePlatform's Maxvalue
                                    state.simulated_hours = max(state.twitter_simulated_hours, state.reddit_simulated_hours)
                                
                                continue
                            
                            action = AgentAction(
                                round_num=action_data.get("round", 0),
                                timestamp=action_data.get("timestamp", datetime.now().isoformat()),
                                platform=platform,
                                agent_id=action_data.get("agent_id", 0),
                                agent_name=action_data.get("agent_name", ""),
                                action_type=action_data.get("action_type", ""),
                                action_args=action_data.get("action_args", {}),
                                result=action_data.get("result"),
                                success=action_data.get("success", True),
                            )
                            state.add_action(action)
                            
                            # UpdateRound
                            if action.round_num and action.round_num > state.current_round:
                                state.current_round = action.round_num
                            
                            # such asforGraph memory update, willActivitySendtoZep
                            if graph_updater:
                                graph_updater.add_activity_from_dict(action_data, platform)
                            
                        except json.JSONDecodeError:
                            pass
                return f.tell()
        except Exception as e:
            logger.warning(f"ReadAction logFailed: {log_path}, error={e}")
            return position
    
    @classmethod
    def _check_all_platforms_completed(cls, state: SimulationRunState) -> bool:
        """
        CheckAllfor's PlatformiswhetherallCompletedSimulated
        
        Checkfor's  actions.jsonl FileiswhetherExistsDeterminePlatformiswhetherwasfor
        
        Returns:
            True such asAllfor's PlatformallCompleted
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, state.simulation_id)
        twitter_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        reddit_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        
        # CheckPlatformwasfor(FileiswhetherExistsDetermine)
        twitter_enabled = os.path.exists(twitter_log)
        reddit_enabled = os.path.exists(reddit_log)
        
        # such asPlatformwasforbutNot completed, thenReturn False
        if twitter_enabled and not state.twitter_completed:
            return False
        if reddit_enabled and not state.reddit_completed:
            return False
        
        # havePlatformwasforCompleted
        return twitter_enabled or reddit_enabled
    
    @classmethod
    def _terminate_process(cls, process: subprocess.Popen, simulation_id: str, timeout: int = 10):
        """
        PlatformTerminateProcessandChild processes
        
        Args:
            process: needTerminate's Process
            simulation_id: SimulatedID(foratLog)
            timeout: WaitProcessExit's Timeout duration(seconds)
        """
        if IS_WINDOWS:
            # Windows: Uses taskkill CommandTerminateProcess tree
            # /F = Force kill, /T = TerminateProcess tree(Child processes)
            logger.info(f"TerminateProcess tree (Windows): simulation={simulation_id}, pid={process.pid}")
            try:
                # firsttry toGraceful termination
                subprocess.run(
                    ['taskkill', '/PID', str(process.pid), '/T'],
                    capture_output=True,
                    timeout=5
                )
                try:
                    process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Force kill
                    logger.warning(f"ProcessnotResponse, Force kill: {simulation_id}")
                    subprocess.run(
                        ['taskkill', '/F', '/PID', str(process.pid), '/T'],
                        capture_output=True,
                        timeout=5
                    )
                    process.wait(timeout=5)
            except Exception as e:
                logger.warning(f"taskkill Failed, try to terminate: {e}")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        else:
            # Unix: UsesProcess groupTerminate
            # atUses start_new_session=True, Process group ID etc.atProcess PID
            pgid = os.getpgid(process.pid)
            logger.info(f"TerminateProcess group (Unix): simulation={simulation_id}, pgid={pgid}")
            
            # firstSend SIGTERM toProcess group
            os.killpg(pgid, signal.SIGTERM)
            
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # such asTimeoutafterEnd, ForceSend SIGKILL
                logger.warning(f"Process groupnotResponse SIGTERM, Force kill: {simulation_id}")
                os.killpg(pgid, signal.SIGKILL)
                process.wait(timeout=5)
    
    @classmethod
    def stop_simulation(cls, simulation_id: str) -> SimulationRunState:
        """StopSimulated"""
        state = cls.get_run_state(simulation_id)
        if not state:
            raise ValueError(f"Simulation not found: {simulation_id}")
        
        if state.runner_status not in [RunnerStatus.RUNNING, RunnerStatus.PAUSED]:
            raise ValueError(f"SimulatednotinRun: {simulation_id}, status={state.runner_status}")
        
        state.runner_status = RunnerStatus.STOPPING
        cls._save_run_state(state)
        
        # TerminateProcess
        process = cls._processes.get(simulation_id)
        if process and process.poll() is None:
            try:
                cls._terminate_process(process, simulation_id)
            except ProcessLookupError:
                # ProcessAlreadynotExists
                pass
            except Exception as e:
                logger.error(f"TerminateProcess groupFailed: {simulation_id}, error={e}")
                # todirectly TerminateProcess
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    process.kill()
        
        state.runner_status = RunnerStatus.STOPPED
        state.twitter_running = False
        state.reddit_running = False
        state.completed_at = datetime.now().isoformat()
        cls._save_run_state(state)
        
        # StopGraph memory updater
        if cls._graph_memory_enabled.get(simulation_id, False):
            try:
                ZepGraphMemoryManager.stop_updater(simulation_id)
                logger.info(f"alreadyStopGraph memory update: simulation_id={simulation_id}")
            except Exception as e:
                logger.error(f"StopGraph memory updaterFailed: {e}")
            cls._graph_memory_enabled.pop(simulation_id, None)
        
        logger.info(f"SimulatedalreadyStop: {simulation_id}")
        return state
    
    @classmethod
    def _read_actions_from_file(
        cls,
        file_path: str,
        default_platform: Optional[str] = None,
        platform_filter: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        fromSingleAction fileinReadactions
        
        Args:
            file_path: Action logFile path
            default_platform: DefaultPlatform(Action recordinno platform FieldUses)
            platform_filter: FilterPlatform
            agent_id: Filter Agent ID
            round_num: FilterRound
        """
        if not os.path.exists(file_path):
            return []
        
        actions = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # SkipAction record(such as simulation_start, round_start, round_end etc. events)
                    if "event_type" in data:
                        continue
                    
                    # Skipno agent_id 's ( Agent actions)
                    if "agent_id" not in data:
                        continue
                    
                    # GetPlatform: firstUsesin's  platform, whetherthenUsesDefaultPlatform
                    record_platform = data.get("platform") or default_platform or ""
                    
                    # Filter
                    if platform_filter and record_platform != platform_filter:
                        continue
                    if agent_id is not None and data.get("agent_id") != agent_id:
                        continue
                    if round_num is not None and data.get("round") != round_num:
                        continue
                    
                    actions.append(AgentAction(
                        round_num=data.get("round", 0),
                        timestamp=data.get("timestamp", ""),
                        platform=record_platform,
                        agent_id=data.get("agent_id", 0),
                        agent_name=data.get("agent_name", ""),
                        action_type=data.get("action_type", ""),
                        action_args=data.get("action_args", {}),
                        result=data.get("result"),
                        success=data.get("success", True),
                    ))
                    
                except json.JSONDecodeError:
                    continue
        
        return actions
    
    @classmethod
    def get_all_actions(
        cls,
        simulation_id: str,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        GetAllPlatform's Action history(Limit)
        
        Args:
            simulation_id: SimulatedID
            platform: FilterPlatform(twitter/reddit)
            agent_id: FilterAgent
            round_num: FilterRound
            
        Returns:
            's Action list(byTimestamp, Newinbefore)
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        actions = []
        
        # Read Twitter Action file(File pathAutomaticSet platform as twitter)
        twitter_actions_log = os.path.join(sim_dir, "twitter", "actions.jsonl")
        if not platform or platform == "twitter":
            actions.extend(cls._read_actions_from_file(
                twitter_actions_log,
                default_platform="twitter",  # Automatic platform Field
                platform_filter=platform,
                agent_id=agent_id, 
                round_num=round_num
            ))
        
        # Read Reddit Action file(File pathAutomaticSet platform as reddit)
        reddit_actions_log = os.path.join(sim_dir, "reddit", "actions.jsonl")
        if not platform or platform == "reddit":
            actions.extend(cls._read_actions_from_file(
                reddit_actions_log,
                default_platform="reddit",  # Automatic platform Field
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            ))
        
        # such asPlatformFilenotExists, try toReadOldFile format
        if not actions:
            actions_log = os.path.join(sim_dir, "actions.jsonl")
            actions = cls._read_actions_from_file(
                actions_log,
                default_platform=None,  # FormatFileinShouldhave platform Field
                platform_filter=platform,
                agent_id=agent_id,
                round_num=round_num
            )
        
        # byTimestamp(Newinbefore)
        actions.sort(key=lambda x: x.timestamp, reverse=True)
        
        return actions
    
    @classmethod
    def get_actions(
        cls,
        simulation_id: str,
        limit: int = 100,
        offset: int = 0,
        platform: Optional[str] = None,
        agent_id: Optional[int] = None,
        round_num: Optional[int] = None
    ) -> List[AgentAction]:
        """
        GetAction history()
        
        Args:
            simulation_id: SimulatedID
            limit: ReturnCountLimit
            offset: Offset
            platform: FilterPlatform
            agent_id: FilterAgent
            round_num: FilterRound
            
        Returns:
            Action list
        """
        actions = cls.get_all_actions(
            simulation_id=simulation_id,
            platform=platform,
            agent_id=agent_id,
            round_num=round_num
        )
        
        # 
        return actions[offset:offset + limit]
    
    @classmethod
    def get_timeline(
        cls,
        simulation_id: str,
        start_round: int = 0,
        end_round: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        GetSimulatedTimeline(byRoundSummary)
        
        Args:
            simulation_id: SimulatedID
            start_round: Round
            end_round: EndRound
            
        Returns:
            per-round's SummaryInformation
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        # byRoundGroup
        rounds: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            round_num = action.round_num
            
            if round_num < start_round:
                continue
            if end_round is not None and round_num > end_round:
                continue
            
            if round_num not in rounds:
                rounds[round_num] = {
                    "round_num": round_num,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "active_agents": set(),
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            r = rounds[round_num]
            
            if action.platform == "twitter":
                r["twitter_actions"] += 1
            else:
                r["reddit_actions"] += 1
            
            r["active_agents"].add(action.agent_id)
            r["action_types"][action.action_type] = r["action_types"].get(action.action_type, 0) + 1
            r["last_action_time"] = action.timestamp
        
        # ConvertasList
        result = []
        for round_num in sorted(rounds.keys()):
            r = rounds[round_num]
            result.append({
                "round_num": round_num,
                "twitter_actions": r["twitter_actions"],
                "reddit_actions": r["reddit_actions"],
                "total_actions": r["twitter_actions"] + r["reddit_actions"],
                "active_agents_count": len(r["active_agents"]),
                "active_agents": list(r["active_agents"]),
                "action_types": r["action_types"],
                "first_action_time": r["first_action_time"],
                "last_action_time": r["last_action_time"],
            })
        
        return result
    
    @classmethod
    def get_agent_stats(cls, simulation_id: str) -> List[Dict[str, Any]]:
        """
        GetEachAgent's Statistics
        
        Returns:
            AgentStatisticsList
        """
        actions = cls.get_actions(simulation_id, limit=10000)
        
        agent_stats: Dict[int, Dict[str, Any]] = {}
        
        for action in actions:
            agent_id = action.agent_id
            
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": action.agent_name,
                    "total_actions": 0,
                    "twitter_actions": 0,
                    "reddit_actions": 0,
                    "action_types": {},
                    "first_action_time": action.timestamp,
                    "last_action_time": action.timestamp,
                }
            
            stats = agent_stats[agent_id]
            stats["total_actions"] += 1
            
            if action.platform == "twitter":
                stats["twitter_actions"] += 1
            else:
                stats["reddit_actions"] += 1
            
            stats["action_types"][action.action_type] = stats["action_types"].get(action.action_type, 0) + 1
            stats["last_action_time"] = action.timestamp
        
        # byactions
        result = sorted(agent_stats.values(), key=lambda x: x["total_actions"], reverse=True)
        
        return result
    
    @classmethod
    def cleanup_simulation_logs(cls, simulation_id: str) -> Dict[str, Any]:
        """
        Clean upSimulated's Run logs(foratForce restartSimulated)
        
        willDeletewithunderFile: 
        - run_state.json
        - twitter/actions.jsonl
        - reddit/actions.jsonl
        - simulation.log
        - stdout.log / stderr.log
        - twitter_simulation.db(SimulatedDatabase)
        - reddit_simulation.db(SimulatedDatabase)
        - env_status.json(Environment status)
        
        : notwillDeleteConfiguration file(simulation_config.json) and  profile File
        
        Args:
            simulation_id: SimulatedID
            
        Returns:
            Clean upResultInformation
        """
        import shutil
        
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        if not os.path.exists(sim_dir):
            return {"success": True, "message": "Simulation directory not found, no cleanup needed"}
        
        cleaned_files = []
        errors = []
        
        # needDelete's File list(DatabaseFile)
        files_to_delete = [
            "run_state.json",
            "simulation.log",
            "stdout.log",
            "stderr.log",
            "twitter_simulation.db",  # Twitter PlatformDatabase
            "reddit_simulation.db",   # Reddit PlatformDatabase
            "env_status.json",        # Environment statusFile
        ]
        
        # needDelete's DirectoryList(ContainsAction log)
        dirs_to_clean = ["twitter", "reddit"]
        
        # DeleteFile
        for filename in files_to_delete:
            file_path = os.path.join(sim_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    cleaned_files.append(filename)
                except Exception as e:
                    errors.append(f"Delete {filename} Failed: {str(e)}")
        
        # Clean upPlatformDirectoryin's Action log
        for dir_name in dirs_to_clean:
            dir_path = os.path.join(sim_dir, dir_name)
            if os.path.exists(dir_path):
                actions_file = os.path.join(dir_path, "actions.jsonl")
                if os.path.exists(actions_file):
                    try:
                        os.remove(actions_file)
                        cleaned_files.append(f"{dir_name}/actions.jsonl")
                    except Exception as e:
                        errors.append(f"Delete {dir_name}/actions.jsonl Failed: {str(e)}")
        
        # Clean upwithinexistin's Run state
        if simulation_id in cls._run_states:
            del cls._run_states[simulation_id]
        
        logger.info(f"Clean upSimulatedLogCompleted: {simulation_id}, DeleteFile: {cleaned_files}")
        
        return {
            "success": len(errors) == 0,
            "cleaned_files": cleaned_files,
            "errors": errors if errors else None
        }
    
    # duplicateClean up's Flag
    _cleanup_done = False
    
    @classmethod
    def cleanup_all_simulations(cls):
        """
        Clean upAllRunin's Simulation process
        
        inServerClosefor, EnsureAllChild processeswasTerminate
        """
        # duplicateClean up
        if cls._cleanup_done:
            return
        cls._cleanup_done = True
        
        # CheckiswhetherhaveContentNeedClean up(avoidProcess's ProcessPrintforLog)
        has_processes = bool(cls._processes)
        has_updaters = bool(cls._graph_memory_enabled)
        
        if not has_processes and not has_updaters:
            return  # noNeedClean up's Content, Return
        
        logger.info("CurrentlyClean upAllSimulation process...")
        
        # firstStopAllGraph memory updater(stop_all withinwillPrintLog)
        try:
            ZepGraphMemoryManager.stop_all()
        except Exception as e:
            logger.error(f"StopGraph memory updaterFailed: {e}")
        cls._graph_memory_enabled.clear()
        
        # Dictionarywithavoidin
        processes = list(cls._processes.items())
        
        for simulation_id, process in processes:
            try:
                if process.poll() is None:  # ProcessinRun
                    logger.info(f"TerminateSimulation process: {simulation_id}, pid={process.pid}")
                    
                    try:
                        # UsesPlatform's ProcessTerminateMethod
                        cls._terminate_process(process, simulation_id, timeout=5)
                    except (ProcessLookupError, OSError):
                        # ProcesscancanAlreadynotExists, try todirectly Terminate
                        try:
                            process.terminate()
                            process.wait(timeout=3)
                        except Exception:
                            process.kill()
                    
                    # Update run_state.json
                    state = cls.get_run_state(simulation_id)
                    if state:
                        state.runner_status = RunnerStatus.STOPPED
                        state.twitter_running = False
                        state.reddit_running = False
                        state.completed_at = datetime.now().isoformat()
                        state.error = "Server shutdown, simulation terminated"
                        cls._save_run_state(state)
                    
                    # Update state.json, willstatusas stopped
                    try:
                        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
                        state_file = os.path.join(sim_dir, "state.json")
                        logger.info(f"try toUpdate state.json: {state_file}")
                        if os.path.exists(state_file):
                            with open(state_file, 'r', encoding='utf-8') as f:
                                state_data = json.load(f)
                            state_data['status'] = 'stopped'
                            state_data['updated_at'] = datetime.now().isoformat()
                            with open(state_file, 'w', encoding='utf-8') as f:
                                json.dump(state_data, f, indent=2, ensure_ascii=False)
                            logger.info(f"alreadyUpdate state.json statusas stopped: {simulation_id}")
                        else:
                            logger.warning(f"state.json notExists: {state_file}")
                    except Exception as state_err:
                        logger.warning(f"Update state.json Failed: {simulation_id}, error={state_err}")
                        
            except Exception as e:
                logger.error(f"Clean upProcessFailed: {simulation_id}, error={e}")
        
        # Clean upFile handles
        for simulation_id, file_handle in list(cls._stdout_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stdout_files.clear()
        
        for simulation_id, file_handle in list(cls._stderr_files.items()):
            try:
                if file_handle:
                    file_handle.close()
            except Exception:
                pass
        cls._stderr_files.clear()
        
        # Clean upwithinexistin's status
        cls._processes.clear()
        cls._action_queues.clear()
        
        logger.info("Simulation processClean upCompleted")
    
    @classmethod
    def register_cleanup(cls):
        """
        RegisterClean upFunction
        
        in Flask forStartfor, EnsureServerCloseClean upAllSimulation process
        """
        global _cleanup_registered
        
        if _cleanup_registered:
            return
        
        # Flask debug Modeunder, in reloader Child processesinRegisterClean up(Runfor's Process)
        # WERKZEUG_RUN_MAIN=true is reloader Child processes
        # such asnotis debug Mode, thennothisEnvironment variables, alsoNeedRegister
        is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
        is_debug_mode = os.environ.get('FLASK_DEBUG') == '1' or os.environ.get('WERKZEUG_RUN_MAIN') is not None
        
        # in debug Modeunder, in reloader Child processesinRegister;  debug ModeunderRegister
        if is_debug_mode and not is_reloader_process:
            _cleanup_registered = True  # MarkalreadyRegister, Child processesthentimestry to
            return
        
        # Savehave's Signal handler
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)
        # SIGHUP in Unix Exists(macOS/Linux), Windows no
        original_sighup = None
        has_sighup = hasattr(signal, 'SIGHUP')
        if has_sighup:
            original_sighup = signal.getsignal(signal.SIGHUP)
        
        def cleanup_handler(signum=None, frame=None):
            """Signal handler: firstClean upSimulation process, thenforProcess"""
            # haveinhaveProcessNeedClean upPrintLog
            if cls._processes or cls._graph_memory_enabled:
                logger.info(f"to {signum}, StartClean up...")
            cls.cleanup_all_simulations()
            
            # forhave's Signal handler, let Flask Exit
            if signum == signal.SIGINT and callable(original_sigint):
                original_sigint(signum, frame)
            elif signum == signal.SIGTERM and callable(original_sigterm):
                original_sigterm(signum, frame)
            elif has_sighup and signum == signal.SIGHUP:
                # SIGHUP: CloseSend
                if callable(original_sighup):
                    original_sighup(signum, frame)
                else:
                    # Defaultas: Exit
                    sys.exit(0)
            else:
                # such asProcessnotcanfor(such as SIG_DFL), thenUsesDefaultas
                raise KeyboardInterrupt
        
        # Register atexit Process(asfor)
        atexit.register(cls.cleanup_all_simulations)
        
        # RegisterSignal handler(onlyinThreadin)
        try:
            # SIGTERM: kill CommandDefault
            signal.signal(signal.SIGTERM, cleanup_handler)
            # SIGINT: Ctrl+C
            signal.signal(signal.SIGINT, cleanup_handler)
            # SIGHUP: Close(only Unix )
            if has_sighup:
                signal.signal(signal.SIGHUP, cleanup_handler)
        except ValueError:
            # notinThreadin, canUses atexit
            logger.warning("RegisterSignal handler(notinThread), onlyUses atexit")
        
        _cleanup_registered = True
    
    @classmethod
    def get_running_simulations(cls) -> List[str]:
        """
        GetAllCurrentlyRun's SimulatedIDList
        """
        running = []
        for sim_id, process in cls._processes.items():
            if process.poll() is None:
                running.append(sim_id)
        return running
    
    # ============== Interview can ==============
    
    @classmethod
    def check_env_alive(cls, simulation_id: str) -> bool:
        """
        CheckSimulation environmentiswhetherAlive(CanReceiveInterviewCommand)

        Args:
            simulation_id: SimulatedID

        Returns:
            True Alive, False alreadyClose
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            return False

        ipc_client = SimulationIPCClient(sim_dir)
        return ipc_client.check_env_alive()

    @classmethod
    def get_env_status_detail(cls, simulation_id: str) -> Dict[str, Any]:
        """
        GetSimulation environment's DetailedstatusInformation

        Args:
            simulation_id: SimulatedID

        Returns:
            Status detailsDictionary, Contains status, twitter_available, reddit_available, timestamp
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        status_file = os.path.join(sim_dir, "env_status.json")
        
        default_status = {
            "status": "stopped",
            "twitter_available": False,
            "reddit_available": False,
            "timestamp": None
        }
        
        if not os.path.exists(status_file):
            return default_status
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return {
                "status": status.get("status", "stopped"),
                "twitter_available": status.get("twitter_available", False),
                "reddit_available": status.get("reddit_available", False),
                "timestamp": status.get("timestamp")
            }
        except (json.JSONDecodeError, OSError):
            return default_status

    @classmethod
    def interview_agent(
        cls,
        simulation_id: str,
        agent_id: int,
        prompt: str,
        platform: str = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        InterviewSingleAgent

        Args:
            simulation_id: SimulatedID
            agent_id: Agent ID
            prompt: Interview questions
            platform: SpecifiedPlatform(optional)
                - "twitter": InterviewTwitterPlatform
                - "reddit": InterviewRedditPlatform
                - None: DualPlatformSimulatedInterviewPlatform, ReturnIntegrateResult
            timeout: Timeout duration(seconds)

        Returns:
            Interview resultsDictionary

        Raises:
            ValueError: Simulation not found or notRun
            TimeoutError: Wait for responseTimeout
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation not found: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"Simulation environment not running or closed, ExecuteInterview: {simulation_id}")

        logger.info(f"SendInterviewCommand: simulation_id={simulation_id}, agent_id={agent_id}, platform={platform}")

        response = ipc_client.send_interview(
            agent_id=agent_id,
            prompt=prompt,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "agent_id": agent_id,
                "prompt": prompt,
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "agent_id": agent_id,
                "prompt": prompt,
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_agents_batch(
        cls,
        simulation_id: str,
        interviews: List[Dict[str, Any]],
        platform: str = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Batch interviewMultipleAgent

        Args:
            simulation_id: SimulatedID
            interviews: Interview list, EachContains {"agent_id": int, "prompt": str, "platform": str(optional)}
            platform: DefaultPlatform(optional, willwasEachInterview's platformcover)
                - "twitter": DefaultInterviewTwitterPlatform
                - "reddit": DefaultInterviewRedditPlatform
                - None: DualPlatformSimulatedEachAgentInterviewPlatform
            timeout: Timeout duration(seconds)

        Returns:
            Interview resultsDictionary

        Raises:
            ValueError: Simulation not found or notRun
            TimeoutError: Wait for responseTimeout
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation not found: {simulation_id}")

        ipc_client = SimulationIPCClient(sim_dir)

        if not ipc_client.check_env_alive():
            raise ValueError(f"Simulation environment not running or closed, ExecuteInterview: {simulation_id}")

        logger.info(f"SendInterviewCommand: simulation_id={simulation_id}, count={len(interviews)}, platform={platform}")

        response = ipc_client.send_batch_interview(
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )

        if response.status.value == "completed":
            return {
                "success": True,
                "interviews_count": len(interviews),
                "result": response.result,
                "timestamp": response.timestamp
            }
        else:
            return {
                "success": False,
                "interviews_count": len(interviews),
                "error": response.error,
                "timestamp": response.timestamp
            }
    
    @classmethod
    def interview_all_agents(
        cls,
        simulation_id: str,
        prompt: str,
        platform: str = None,
        timeout: float = 180.0
    ) -> Dict[str, Any]:
        """
        InterviewAllAgent(Interview)

        UsesSame's QuestionInterviewSimulatedin's AllAgent

        Args:
            simulation_id: SimulatedID
            prompt: Interview questions(AllAgentUsesSameQuestion)
            platform: SpecifiedPlatform(optional)
                - "twitter": InterviewTwitterPlatform
                - "reddit": InterviewRedditPlatform
                - None: DualPlatformSimulatedEachAgentInterviewPlatform
            timeout: Timeout duration(seconds)

        Returns:
            Interview resultsDictionary
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation not found: {simulation_id}")

        # fromConfiguration fileGetAllAgentInformation
        config_path = os.path.join(sim_dir, "simulation_config.json")
        if not os.path.exists(config_path):
            raise ValueError(f"Simulation configurationnotExists: {simulation_id}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        agent_configs = config.get("agent_configs", [])
        if not agent_configs:
            raise ValueError(f"Simulation configurationinnoAgent: {simulation_id}")

        # BuildInterview list
        interviews = []
        for agent_config in agent_configs:
            agent_id = agent_config.get("agent_id")
            if agent_id is not None:
                interviews.append({
                    "agent_id": agent_id,
                    "prompt": prompt
                })

        logger.info(f"SendInterviewCommand: simulation_id={simulation_id}, agent_count={len(interviews)}, platform={platform}")

        return cls.interview_agents_batch(
            simulation_id=simulation_id,
            interviews=interviews,
            platform=platform,
            timeout=timeout
        )
    
    @classmethod
    def close_simulation_env(
        cls,
        simulation_id: str,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        CloseSimulation environment(notisStopSimulation process)
        
        toSimulatedSendCloseCommand, Graceful exitWaitCommandMode
        
        Args:
            simulation_id: SimulatedID
            timeout: Timeout duration(seconds)
            
        Returns:
            operationsResultDictionary
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        if not os.path.exists(sim_dir):
            raise ValueError(f"Simulation not found: {simulation_id}")
        
        ipc_client = SimulationIPCClient(sim_dir)
        
        if not ipc_client.check_env_alive():
            return {
                "success": True,
                "message": "AlreadyClose"
            }
        
        logger.info(f"SendCloseCommand: simulation_id={simulation_id}")
        
        try:
            response = ipc_client.send_close_env(timeout=timeout)
            
            return {
                "success": response.status.value == "completed",
                "message": "CloseCommandalreadySend",
                "result": response.result,
                "timestamp": response.timestamp
            }
        except TimeoutError:
            # TimeoutcancanisasCurrentlyClose
            return {
                "success": True,
                "message": "CloseCommandalreadySend(Wait for responseTimeout, cancanCurrentlyClose)"
            }
    
    @classmethod
    def _get_interview_history_from_db(
        cls,
        db_path: str,
        platform_name: str,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """fromSingleDatabaseGetInterview"""
        import sqlite3
        
        if not os.path.exists(db_path):
            return []
        
        results = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if agent_id is not None:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview' AND user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (agent_id, limit))
            else:
                cursor.execute("""
                    SELECT user_id, info, created_at
                    FROM trace
                    WHERE action = 'interview'
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
            
            for user_id, info_json, created_at in cursor.fetchall():
                try:
                    info = json.loads(info_json) if info_json else {}
                except json.JSONDecodeError:
                    info = {"raw": info_json}
                
                results.append({
                    "agent_id": user_id,
                    "response": info.get("response", info),
                    "prompt": info.get("prompt", ""),
                    "timestamp": created_at,
                    "platform": platform_name
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"ReadInterviewFailed ({platform_name}): {e}")
        
        return results

    @classmethod
    def get_interview_history(
        cls,
        simulation_id: str,
        platform: str = None,
        agent_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        GetInterview(fromDatabaseRead)
        
        Args:
            simulation_id: SimulatedID
            platform: PlatformType(reddit/twitter/None)
                - "reddit": GetRedditPlatform's 
                - "twitter": GetTwitterPlatform's 
                - None: GetPlatform's All
            agent_id: SpecifiedAgent ID(optional, GetAgent's )
            limit: EachPlatformReturnCountLimit
            
        Returns:
            InterviewList
        """
        sim_dir = os.path.join(cls.RUN_STATE_DIR, simulation_id)
        
        results = []
        
        # DetermineneedQuery's Platform
        if platform in ("reddit", "twitter"):
            platforms = [platform]
        else:
            # notSpecifiedplatform, QueryPlatform
            platforms = ["twitter", "reddit"]
        
        for p in platforms:
            db_path = os.path.join(sim_dir, f"{p}_simulation.db")
            platform_results = cls._get_interview_history_from_db(
                db_path=db_path,
                platform_name=p,
                agent_id=agent_id,
                limit=limit
            )
            results.extend(platform_results)
        
        # byTime
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # such asQueryMultiplePlatform, LimitTotal
        if len(platforms) > 1 and len(results) > limit:
            results = results[:limit]
        
        return results

