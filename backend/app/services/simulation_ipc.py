"""
SimulatedIPC
foratFlaskafter and SimulatedScriptbetween's Processbetween

File's Command/ResponseMode: 
1. FlaskWriteCommandto commands/ Directory
2. SimulatedScriptPollCommandDirectory, ExecuteCommandWriteResponseto responses/ Directory
3. FlaskPollResponseDirectoryGetResult
"""

import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..utils.logger import get_logger

logger = get_logger('deepak.simulation_ipc')


class CommandType(str, Enum):
    """Command type"""
    INTERVIEW = "interview"           # SingleAgentInterview
    BATCH_INTERVIEW = "batch_interview"  # Batch interview
    CLOSE_ENV = "close_env"           # Close


class CommandStatus(str, Enum):
    """Commandstatus"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class IPCCommand:
    """IPCCommand"""
    command_id: str
    command_type: CommandType
    args: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "command_type": self.command_type.value,
            "args": self.args,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPCCommand':
        return cls(
            command_id=data["command_id"],
            command_type=CommandType(data["command_type"]),
            args=data.get("args", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class IPCResponse:
    """IPCResponse"""
    command_id: str
    status: CommandStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "command_id": self.command_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPCResponse':
        return cls(
            command_id=data["command_id"],
            status=CommandStatus(data["status"]),
            result=data.get("result"),
            error=data.get("error"),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


class SimulationIPCClient:
    """
    SimulatedIPCClient(FlaskUses)
    
    forattoSimulation processSend commandWait for response
    """
    
    def __init__(self, simulation_dir: str):
        """
        InitializeIPCClient
        
        Args:
            simulation_dir: SimulatedData directory
        """
        self.simulation_dir = simulation_dir
        self.commands_dir = os.path.join(simulation_dir, "ipc_commands")
        self.responses_dir = os.path.join(simulation_dir, "ipc_responses")
        
        # EnsureDirectoryExists
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
    
    def send_command(
        self,
        command_type: CommandType,
        args: Dict[str, Any],
        timeout: float = 60.0,
        poll_interval: float = 0.5
    ) -> IPCResponse:
        """
        Send commandWait for response
        
        Args:
            command_type: Command type
            args: Command parameters
            timeout: Timeout duration(seconds)
            poll_interval: Poll interval(seconds)
            
        Returns:
            IPCResponse
            
        Raises:
            TimeoutError: Wait for responseTimeout
        """
        command_id = str(uuid.uuid4())
        command = IPCCommand(
            command_id=command_id,
            command_type=command_type,
            args=args
        )
        
        # WriteCommandFile
        command_file = os.path.join(self.commands_dir, f"{command_id}.json")
        with open(command_file, 'w', encoding='utf-8') as f:
            json.dump(command.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"SendIPCCommand: {command_type.value}, command_id={command_id}")
        
        # Wait for response
        response_file = os.path.join(self.responses_dir, f"{command_id}.json")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if os.path.exists(response_file):
                try:
                    with open(response_file, 'r', encoding='utf-8') as f:
                        response_data = json.load(f)
                    response = IPCResponse.from_dict(response_data)
                    
                    # Clean upCommand and ResponseFile
                    try:
                        os.remove(command_file)
                        os.remove(response_file)
                    except OSError:
                        pass
                    
                    logger.info(f"toIPCResponse: command_id={command_id}, status={response.status.value}")
                    return response
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"ParseResponseFailed: {e}")
            
            time.sleep(poll_interval)
        
        # Timeout
        logger.error(f"WaitIPCResponseTimeout: command_id={command_id}")
        
        # Clean upCommandFile
        try:
            os.remove(command_file)
        except OSError:
            pass
        
        raise TimeoutError(f"WaitCommandResponseTimeout ({timeout}seconds)")
    
    def send_interview(
        self,
        agent_id: int,
        prompt: str,
        platform: str = None,
        timeout: float = 60.0
    ) -> IPCResponse:
        """
        SendSingleAgentInterviewCommand
        
        Args:
            agent_id: Agent ID
            prompt: Interview questions
            platform: SpecifiedPlatform(optional)
                - "twitter": InterviewTwitterPlatform
                - "reddit": InterviewRedditPlatform  
                - None: DualPlatformSimulatedInterviewPlatform, PlatformSimulatedInterviewPlatform
            timeout: Timeout duration
            
        Returns:
            IPCResponse, resultFieldContainsInterview results
        """
        args = {
            "agent_id": agent_id,
            "prompt": prompt
        }
        if platform:
            args["platform"] = platform
            
        return self.send_command(
            command_type=CommandType.INTERVIEW,
            args=args,
            timeout=timeout
        )
    
    def send_batch_interview(
        self,
        interviews: List[Dict[str, Any]],
        platform: str = None,
        timeout: float = 120.0
    ) -> IPCResponse:
        """
        SendBatch interviewCommand
        
        Args:
            interviews: Interview list, EachContains {"agent_id": int, "prompt": str, "platform": str(optional)}
            platform: DefaultPlatform(optional, willwasEachInterview's platformcover)
                - "twitter": DefaultInterviewTwitterPlatform
                - "reddit": DefaultInterviewRedditPlatform
                - None: DualPlatformSimulatedEachAgentInterviewPlatform
            timeout: Timeout duration
            
        Returns:
            IPCResponse, resultFieldContainsAllInterview results
        """
        args = {"interviews": interviews}
        if platform:
            args["platform"] = platform
            
        return self.send_command(
            command_type=CommandType.BATCH_INTERVIEW,
            args=args,
            timeout=timeout
        )
    
    def send_close_env(self, timeout: float = 30.0) -> IPCResponse:
        """
        SendCloseCommand
        
        Args:
            timeout: Timeout duration
            
        Returns:
            IPCResponse
        """
        return self.send_command(
            command_type=CommandType.CLOSE_ENV,
            args={},
            timeout=timeout
        )
    
    def check_env_alive(self) -> bool:
        """
        CheckSimulation environmentiswhetherAlive
        
        Check env_status.json FileDetermine
        """
        status_file = os.path.join(self.simulation_dir, "env_status.json")
        if not os.path.exists(status_file):
            return False
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return status.get("status") == "alive"
        except (json.JSONDecodeError, OSError):
            return False


class SimulationIPCServer:
    """
    SimulatedIPCServer(SimulatedScriptUses)
    
    PollCommandDirectory, ExecuteCommandReturnResponse
    """
    
    def __init__(self, simulation_dir: str):
        """
        InitializeIPCServer
        
        Args:
            simulation_dir: SimulatedData directory
        """
        self.simulation_dir = simulation_dir
        self.commands_dir = os.path.join(simulation_dir, "ipc_commands")
        self.responses_dir = os.path.join(simulation_dir, "ipc_responses")
        
        # EnsureDirectoryExists
        os.makedirs(self.commands_dir, exist_ok=True)
        os.makedirs(self.responses_dir, exist_ok=True)
        
        # Environment status
        self._running = False
    
    def start(self):
        """MarkServerasRun state"""
        self._running = True
        self._update_env_status("alive")
    
    def stop(self):
        """MarkServerasStopstatus"""
        self._running = False
        self._update_env_status("stopped")
    
    def _update_env_status(self, status: str):
        """UpdateEnvironment statusFile"""
        status_file = os.path.join(self.simulation_dir, "env_status.json")
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": status,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
    
    def poll_commands(self) -> Optional[IPCCommand]:
        """
        PollCommandDirectory, ReturnProcess's Command
        
        Returns:
            IPCCommand  or  None
        """
        if not os.path.exists(self.commands_dir):
            return None
        
        # byTimeGetCommandFile
        command_files = []
        for filename in os.listdir(self.commands_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.commands_dir, filename)
                command_files.append((filepath, os.path.getmtime(filepath)))
        
        command_files.sort(key=lambda x: x[1])
        
        for filepath, _ in command_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return IPCCommand.from_dict(data)
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning(f"ReadCommandFileFailed: {filepath}, {e}")
                continue
        
        return None
    
    def send_response(self, response: IPCResponse):
        """
        SendResponse
        
        Args:
            response: IPCResponse
        """
        response_file = os.path.join(self.responses_dir, f"{response.command_id}.json")
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(response.to_dict(), f, ensure_ascii=False, indent=2)
        
        # DeleteCommandFile
        command_file = os.path.join(self.commands_dir, f"{response.command_id}.json")
        try:
            os.remove(command_file)
        except OSError:
            pass
    
    def send_success(self, command_id: str, result: Dict[str, Any]):
        """SendSuccessfullyResponse"""
        self.send_response(IPCResponse(
            command_id=command_id,
            status=CommandStatus.COMPLETED,
            result=result
        ))
    
    def send_error(self, command_id: str, error: str):
        """SendResponse"""
        self.send_response(IPCResponse(
            command_id=command_id,
            status=CommandStatus.FAILED,
            error=error
        ))
