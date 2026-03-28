"""
ZepRetrieve
Graph search, NodeRead, Queryetc., Report AgentUses

CoreRetrieve(after): 
1. InsightForge(Deep insightRetrieve)- 's Retrieve, Auto-generateSub-queriesDimensionRetrieve
2. PanoramaSearch(Broad search)- Get, Content
3. QuickSearch(Search)- Retrieve
"""

import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from zep_cloud.client import Zep

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient
from ..utils.zep_paging import fetch_all_nodes, fetch_all_edges

logger = get_logger('deepak.zep_tools')


@dataclass
class SearchResult:
    """Search results"""
    facts: List[str]
    edges: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]]
    query: str
    total_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "facts": self.facts,
            "edges": self.edges,
            "nodes": self.nodes,
            "query": self.query,
            "total_count": self.total_count
        }
    
    def to_text(self) -> str:
        """ConvertasText format, LLM"""
        text_parts = [f"Search query: {self.query}", f"to {self.total_count} Related information"]
        
        if self.facts:
            text_parts.append("\n### Related facts:")
            for i, fact in enumerate(self.facts, 1):
                text_parts.append(f"{i}. {fact}")
        
        return "\n".join(text_parts)


@dataclass
class NodeInfo:
    """NodeInformation"""
    uuid: str
    name: str
    labels: List[str]
    summary: str
    attributes: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "labels": self.labels,
            "summary": self.summary,
            "attributes": self.attributes
        }
    
    def to_text(self) -> str:
        """ConvertasText format"""
        entity_type = next((l for l in self.labels if l not in ["Entity", "Node"]), "Unknown type")
        return f": {self.name} (Type: {entity_type})\nSummary: {self.summary}"


@dataclass
class EdgeInfo:
    """Information"""
    uuid: str
    name: str
    fact: str
    source_node_uuid: str
    target_node_uuid: str
    source_node_name: Optional[str] = None
    target_node_name: Optional[str] = None
    # Time information
    created_at: Optional[str] = None
    valid_at: Optional[str] = None
    invalid_at: Optional[str] = None
    expired_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "fact": self.fact,
            "source_node_uuid": self.source_node_uuid,
            "target_node_uuid": self.target_node_uuid,
            "source_node_name": self.source_node_name,
            "target_node_name": self.target_node_name,
            "created_at": self.created_at,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "expired_at": self.expired_at
        }
    
    def to_text(self, include_temporal: bool = False) -> str:
        """ConvertasText format"""
        source = self.source_node_name or self.source_node_uuid[:8]
        target = self.target_node_name or self.target_node_uuid[:8]
        base_text = f"Relationship: {source} --[{self.name}]--> {target}\nfacts: {self.fact}"
        
        if include_temporal:
            valid_at = self.valid_at or "Unknown"
            invalid_at = self.invalid_at or "Present"
            base_text += f"\nValidity period: {valid_at} - {invalid_at}"
            if self.expired_at:
                base_text += f" (Expired: {self.expired_at})"
        
        return base_text
    
    @property
    def is_expired(self) -> bool:
        """iswhetherExpired"""
        return self.expired_at is not None
    
    @property
    def is_invalid(self) -> bool:
        """iswhetherInvalid"""
        return self.invalid_at is not None


@dataclass
class InsightForgeResult:
    """
    Deep insightRetrieveResult (InsightForge)
    ContainsMultipleSub-queries's RetrieveResult, withandAnalysis
    """
    query: str
    simulation_requirement: str
    sub_queries: List[str]
    
    # per-DimensionRetrieveResult
    semantic_facts: List[str] = field(default_factory=list)  # Search results
    entity_insights: List[Dict[str, Any]] = field(default_factory=list)  # Entity insights
    relationship_chains: List[str] = field(default_factory=list)  # Relationship chains
    
    # Statistics
    total_facts: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "simulation_requirement": self.simulation_requirement,
            "sub_queries": self.sub_queries,
            "semantic_facts": self.semantic_facts,
            "entity_insights": self.entity_insights,
            "relationship_chains": self.relationship_chains,
            "total_facts": self.total_facts,
            "total_entities": self.total_entities,
            "total_relationships": self.total_relationships
        }
    
    def to_text(self) -> str:
        """ConvertasDetailed's Text format, LLM"""
        text_parts = [
            f"## Future predictionAnalysis",
            f"Analysis question: {self.query}",
            f"Prediction scenario: {self.simulation_requirement}",
            f"\n### Prediction dataStatistics",
            f"- Prediction facts: {self.total_facts}",
            f"- and: {self.total_entities}",
            f"- Relationship chains: {self.total_relationships}"
        ]
        
        # Sub-queries
        if self.sub_queries:
            text_parts.append(f"\n### Analyzed sub-queries")
            for i, sq in enumerate(self.sub_queries, 1):
                text_parts.append(f"{i}. {sq}")
        
        # Search results
        if self.semantic_facts:
            text_parts.append(f"\n### [Key facts](inReportinCitethisOriginal)")
            for i, fact in enumerate(self.semantic_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")
        
        # Entity insights
        if self.entity_insights:
            text_parts.append(f"\n### [Core entities]")
            for entity in self.entity_insights:
                text_parts.append(f"- **{entity.get('name', 'Unknown')}** ({entity.get('type', '')})")
                if entity.get('summary'):
                    text_parts.append(f"  Summary: \"{entity.get('summary')}\"")
                if entity.get('related_facts'):
                    text_parts.append(f"  Related facts: {len(entity.get('related_facts', []))}")
        
        # Relationship chains
        if self.relationship_chains:
            text_parts.append(f"\n### [Relationship chains]")
            for chain in self.relationship_chains:
                text_parts.append(f"- {chain}")
        
        return "\n".join(text_parts)


@dataclass
class PanoramaResult:
    """
    Search results (Panorama)
    ContainsAllRelated information, Content
    """
    query: str
    
    # AllNode
    all_nodes: List[NodeInfo] = field(default_factory=list)
    # All('s )
    all_edges: List[EdgeInfo] = field(default_factory=list)
    # CurrentActive's facts
    active_facts: List[str] = field(default_factory=list)
    # Expired/'s facts()
    historical_facts: List[str] = field(default_factory=list)
    
    # Statistics
    total_nodes: int = 0
    total_edges: int = 0
    active_count: int = 0
    historical_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "all_nodes": [n.to_dict() for n in self.all_nodes],
            "all_edges": [e.to_dict() for e in self.all_edges],
            "active_facts": self.active_facts,
            "historical_facts": self.historical_facts,
            "total_nodes": self.total_nodes,
            "total_edges": self.total_edges,
            "active_count": self.active_count,
            "historical_count": self.historical_count
        }
    
    def to_text(self) -> str:
        """ConvertasText format(Version, nottruncate)"""
        text_parts = [
            f"## Search results(notPanoramic view)",
            f"Query: {self.query}",
            f"\n### Statistics",
            f"- Node: {self.total_nodes}",
            f"- : {self.total_edges}",
            f"- CurrentActive facts: {self.active_count}",
            f"- /Expired facts: {self.historical_count}"
        ]
        
        # CurrentActive's facts(Output, nottruncate)
        if self.active_facts:
            text_parts.append(f"\n### [CurrentActive facts](SimulatedResultOriginal)")
            for i, fact in enumerate(self.active_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")
        
        # /Expired facts(Output, nottruncate)
        if self.historical_facts:
            text_parts.append(f"\n### [/Expired facts]()")
            for i, fact in enumerate(self.historical_facts, 1):
                text_parts.append(f"{i}. \"{fact}\"")
        
        # (Output, nottruncate)
        if self.all_nodes:
            text_parts.append(f"\n### [and]")
            for node in self.all_nodes:
                entity_type = next((l for l in node.labels if l not in ["Entity", "Node"]), "")
                text_parts.append(f"- **{node.name}** ({entity_type})")
        
        return "\n".join(text_parts)


@dataclass
class AgentInterview:
    """SingleAgent's Interview results"""
    agent_name: str
    agent_role: str  # RoleType(such as: , , etc.)
    agent_bio: str  # Bio
    question: str  # Interview questions
    response: str  # InterviewResponse
    key_quotes: List[str] = field(default_factory=list)  # Key quotes
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "agent_bio": self.agent_bio,
            "question": self.question,
            "response": self.response,
            "key_quotes": self.key_quotes
        }
    
    def to_text(self) -> str:
        text = f"**{self.agent_name}** ({self.agent_role})\n"
        # Display's agent_bio, nottruncate
        text += f"_Bio: {self.agent_bio}_\n\n"
        text += f"**Q:** {self.question}\n\n"
        text += f"**A:** {self.response}\n"
        if self.key_quotes:
            text += "\n**Key quotes:**\n"
            for quote in self.key_quotes:
                # Clean upvariousquotation marks
                clean_quote = quote.replace('\u201c', '').replace('\u201d', '').replace('"', '')
                clean_quote = clean_quote.replace('\u300c', '').replace('\u300d', '')
                clean_quote = clean_quote.strip()
                # remove's punctuation
                while clean_quote and clean_quote[0] in ', ,; ;: :, . ! ? \n\r\t ':
                    clean_quote = clean_quote[1:]
                # FilterContainsQuestionnumber's junkContent(Question1-9)
                skip = False
                for d in '123456789':
                    if f'\u95ee\u9898{d}' in clean_quote:
                        skip = True
                        break
                if skip:
                    continue
                # truncate longContent(byperiodtruncate, hard truncation)
                if len(clean_quote) > 150:
                    dot_pos = clean_quote.find('\u3002', 80)
                    if dot_pos > 0:
                        clean_quote = clean_quote[:dot_pos + 1]
                    else:
                        clean_quote = clean_quote[:147] + "..."
                if clean_quote and len(clean_quote) >= 10:
                    text += f'> "{clean_quote}"\n'
        return text


@dataclass
class InterviewResult:
    """
    Interview results (Interview)
    ContainsMultipleSimulatedAgent's InterviewResponse
    """
    interview_topic: str  # Interview topic
    interview_questions: List[str]  # Interview questionsList
    
    # InterviewSelect's Agent
    selected_agents: List[Dict[str, Any]] = field(default_factory=list)
    # per-Agent's InterviewResponse
    interviews: List[AgentInterview] = field(default_factory=list)
    
    # SelectAgent's 
    selection_reasoning: str = ""
    # Integrateafter's Interview summary
    summary: str = ""
    
    # Statistics
    total_agents: int = 0
    interviewed_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "interview_topic": self.interview_topic,
            "interview_questions": self.interview_questions,
            "selected_agents": self.selected_agents,
            "interviews": [i.to_dict() for i in self.interviews],
            "selection_reasoning": self.selection_reasoning,
            "summary": self.summary,
            "total_agents": self.total_agents,
            "interviewed_count": self.interviewed_count
        }
    
    def to_text(self) -> str:
        """ConvertasDetailed's Text format, LLM and ReportCite"""
        text_parts = [
            "## Interview report",
            f"**Interview topic:** {self.interview_topic}",
            f"**Interview:** {self.interviewed_count} / {self.total_agents} SimulatedAgent",
            "\n### InterviewObjectSelect",
            self.selection_reasoning or "(Auto-select)",
            "\n---",
            "\n### Interview transcripts",
        ]

        if self.interviews:
            for i, interview in enumerate(self.interviews, 1):
                text_parts.append(f"\n#### Interview #{i}: {interview.agent_name}")
                text_parts.append(interview.to_text())
                text_parts.append("\n---")
        else:
            text_parts.append("(Interview)\n\n---")

        text_parts.append("\n### Interview summarywithCoreViewpoint")
        text_parts.append(self.summary or "(Summary)")

        return "\n".join(text_parts)


class ZepToolsService:
    """
    ZepRetrieve
    
    [CoreRetrieve - after]
    1. insight_forge - Deep insightRetrieve(, Auto-generateSub-queries, DimensionRetrieve)
    2. panorama_search - Broad search(Get, Content)
    3. quick_search - Search(Retrieve)
    4. interview_agents - Deep interview(InterviewSimulatedAgent, GetPerspectiveViewpoint)
    
    [Basic]
    - search_graph - Graph semantic search
    - get_all_nodes - GetGraphAllNode
    - get_all_edges - GetGraphAll(Time information)
    - get_node_detail - GetNodeDetailed information
    - get_node_edges - GetNode's 
    - get_entities_by_type - byTypeGet
    - get_entity_summary - Get's Relationship summary
    """
    
    # RetryConfiguration
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0
    
    def __init__(self, api_key: Optional[str] = None, llm_client: Optional[LLMClient] = None):
        self.api_key = api_key or Config.ZEP_API_KEY
        if not self.api_key:
            raise ValueError("ZEP_API_KEY not configured")
        
        self.client = Zep(api_key=self.api_key)
        # LLMClientforatInsightForgeGenerateSub-queries
        self._llm_client = llm_client
        logger.info("ZepToolsService InitializeCompleted")
    
    @property
    def llm(self) -> LLMClient:
        """DelayInitializeLLMClient"""
        if self._llm_client is None:
            self._llm_client = LLMClient()
        return self._llm_client
    
    def _call_with_retry(self, func, operation_name: str, max_retries: int = None):
        """Retry mechanism's APIfor"""
        max_retries = max_retries or self.MAX_RETRIES
        last_exception = None
        delay = self.RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Zep {operation_name}  {attempt + 1} timestry toFailed: {str(e)[:100]}, "
                        f"{delay:.1f}secondsafterRetry..."
                    )
                    time.sleep(delay)
                    delay *= 2
                else:
                    logger.error(f"Zep {operation_name} in {max_retries} timestry toafterFailed: {str(e)}")
        
        raise last_exception
    
    def search_graph(
        self, 
        graph_id: str, 
        query: str, 
        limit: int = 10,
        scope: str = "edges"
    ) -> SearchResult:
        """
        Graph semantic search
        
        UsesHybrid search(+BM25)inGraphinSearchRelated information. 
        such asZep Cloud's search APInotcanfor, thenfallbackasKeyword matching. 
        
        Args:
            graph_id: GraphID (Standalone Graph)
            query: Search query
            limit: ReturnResultCount
            scope: Search scope, "edges"  or  "nodes"
            
        Returns:
            SearchResult: Search results
        """
        logger.info(f"Graph search: graph_id={graph_id}, query={query[:50]}...")
        
        # try toUsesZep Cloud Search API
        try:
            search_results = self._call_with_retry(
                func=lambda: self.client.graph.search(
                    graph_id=graph_id,
                    query=query,
                    limit=limit,
                    scope=scope,
                    reranker="cross_encoder"
                ),
                operation_name=f"Graph search(graph={graph_id})"
            )
            
            facts = []
            edges = []
            nodes = []
            
            # ParseSearch results
            if hasattr(search_results, 'edges') and search_results.edges:
                for edge in search_results.edges:
                    if hasattr(edge, 'fact') and edge.fact:
                        facts.append(edge.fact)
                    edges.append({
                        "uuid": getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', ''),
                        "name": getattr(edge, 'name', ''),
                        "fact": getattr(edge, 'fact', ''),
                        "source_node_uuid": getattr(edge, 'source_node_uuid', ''),
                        "target_node_uuid": getattr(edge, 'target_node_uuid', ''),
                    })
            
            # ParseNodeSearch results
            if hasattr(search_results, 'nodes') and search_results.nodes:
                for node in search_results.nodes:
                    nodes.append({
                        "uuid": getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                        "name": getattr(node, 'name', ''),
                        "labels": getattr(node, 'labels', []),
                        "summary": getattr(node, 'summary', ''),
                    })
                    # NodeSummaryalsofacts
                    if hasattr(node, 'summary') and node.summary:
                        facts.append(f"[{node.name}]: {node.summary}")
            
            logger.info(f"SearchCompleted: to {len(facts)} Related facts")
            
            return SearchResult(
                facts=facts,
                edges=edges,
                nodes=nodes,
                query=query,
                total_count=len(facts)
            )
            
        except Exception as e:
            logger.warning(f"Zep Search APIFailed, fallbackasLocal search: {str(e)}")
            # fallback: UsesKeyword matchingSearch
            return self._local_search(graph_id, query, limit, scope)
    
    def _local_search(
        self, 
        graph_id: str, 
        query: str, 
        limit: int = 10,
        scope: str = "edges"
    ) -> SearchResult:
        """
        Keyword matchingSearch(asZep Search API's fallbackSolution)
        
        GetAll/Node, afterinKeyword matching
        
        Args:
            graph_id: GraphID
            query: Search query
            limit: ReturnResultCount
            scope: Search scope
            
        Returns:
            SearchResult: Search results
        """
        logger.info(f"UsesLocal search: query={query[:30]}...")
        
        facts = []
        edges_result = []
        nodes_result = []
        
        # ExtractQueryword(tokenization)
        query_lower = query.lower()
        keywords = [w.strip() for w in query_lower.replace(',', ' ').replace(', ', ' ').split() if len(w.strip()) > 1]
        
        def match_score(text: str) -> int:
            """CalculateTextwithQuery's Match"""
            if not text:
                return 0
            text_lower = text.lower()
            # completelyMatchQuery
            if query_lower in text_lower:
                return 100
            # Keyword matching
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 10
            return score
        
        try:
            if scope in ["edges", "both"]:
                # GetAllMatch
                all_edges = self.get_all_edges(graph_id)
                scored_edges = []
                for edge in all_edges:
                    score = match_score(edge.fact) + match_score(edge.name)
                    if score > 0:
                        scored_edges.append((score, edge))
                
                # by
                scored_edges.sort(key=lambda x: x[0], reverse=True)
                
                for score, edge in scored_edges[:limit]:
                    if edge.fact:
                        facts.append(edge.fact)
                    edges_result.append({
                        "uuid": edge.uuid,
                        "name": edge.name,
                        "fact": edge.fact,
                        "source_node_uuid": edge.source_node_uuid,
                        "target_node_uuid": edge.target_node_uuid,
                    })
            
            if scope in ["nodes", "both"]:
                # GetAllNodeMatch
                all_nodes = self.get_all_nodes(graph_id)
                scored_nodes = []
                for node in all_nodes:
                    score = match_score(node.name) + match_score(node.summary)
                    if score > 0:
                        scored_nodes.append((score, node))
                
                scored_nodes.sort(key=lambda x: x[0], reverse=True)
                
                for score, node in scored_nodes[:limit]:
                    nodes_result.append({
                        "uuid": node.uuid,
                        "name": node.name,
                        "labels": node.labels,
                        "summary": node.summary,
                    })
                    if node.summary:
                        facts.append(f"[{node.name}]: {node.summary}")
            
            logger.info(f"Local searchCompleted: to {len(facts)} Related facts")
            
        except Exception as e:
            logger.error(f"Local searchFailed: {str(e)}")
        
        return SearchResult(
            facts=facts,
            edges=edges_result,
            nodes=nodes_result,
            query=query,
            total_count=len(facts)
        )
    
    def get_all_nodes(self, graph_id: str) -> List[NodeInfo]:
        """
        GetGraph's AllNode(Paginated fetch)

        Args:
            graph_id: GraphID

        Returns:
            NodeList
        """
        logger.info(f"GetGraph {graph_id} 's AllNode...")

        nodes = fetch_all_nodes(self.client, graph_id)

        result = []
        for node in nodes:
            node_uuid = getattr(node, 'uuid_', None) or getattr(node, 'uuid', None) or ""
            result.append(NodeInfo(
                uuid=str(node_uuid) if node_uuid else "",
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {}
            ))

        logger.info(f"Getto {len(result)} Node")
        return result

    def get_all_edges(self, graph_id: str, include_temporal: bool = True) -> List[EdgeInfo]:
        """
        GetGraph's All(Paginated fetch, ContainsTime information)

        Args:
            graph_id: GraphID
            include_temporal: iswhetherContainsTime information(DefaultTrue)

        Returns:
            List(Containscreated_at, valid_at, invalid_at, expired_at)
        """
        logger.info(f"GetGraph {graph_id} 's All...")

        edges = fetch_all_edges(self.client, graph_id)

        result = []
        for edge in edges:
            edge_uuid = getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', None) or ""
            edge_info = EdgeInfo(
                uuid=str(edge_uuid) if edge_uuid else "",
                name=edge.name or "",
                fact=edge.fact or "",
                source_node_uuid=edge.source_node_uuid or "",
                target_node_uuid=edge.target_node_uuid or ""
            )

            # Time information
            if include_temporal:
                edge_info.created_at = getattr(edge, 'created_at', None)
                edge_info.valid_at = getattr(edge, 'valid_at', None)
                edge_info.invalid_at = getattr(edge, 'invalid_at', None)
                edge_info.expired_at = getattr(edge, 'expired_at', None)

            result.append(edge_info)

        logger.info(f"Getto {len(result)} ")
        return result
    
    def get_node_detail(self, node_uuid: str) -> Optional[NodeInfo]:
        """
        GetSingleNode's Detailed information
        
        Args:
            node_uuid: NodeUUID
            
        Returns:
            NodeInformation or None
        """
        logger.info(f"GetNode: {node_uuid[:8]}...")
        
        try:
            node = self._call_with_retry(
                func=lambda: self.client.graph.node.get(uuid_=node_uuid),
                operation_name=f"GetNode(uuid={node_uuid[:8]}...)"
            )
            
            if not node:
                return None
            
            return NodeInfo(
                uuid=getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {}
            )
        except Exception as e:
            logger.error(f"GetNodeFailed: {str(e)}")
            return None
    
    def get_node_edges(self, graph_id: str, node_uuid: str) -> List[EdgeInfo]:
        """
        GetNode's All
        
        GetGraphAll, afterFilterwithSpecifiedNode's 
        
        Args:
            graph_id: GraphID
            node_uuid: NodeUUID
            
        Returns:
            List
        """
        logger.info(f"GetNode {node_uuid[:8]}... 's Related edges")
        
        try:
            # GetGraphAll, afterFilter
            all_edges = self.get_all_edges(graph_id)
            
            result = []
            for edge in all_edges:
                # CheckiswhetherwithSpecifiedNode(as or )
                if edge.source_node_uuid == node_uuid or edge.target_node_uuid == node_uuid:
                    result.append(edge)
            
            logger.info(f"to {len(result)} withNode's ")
            return result
            
        except Exception as e:
            logger.warning(f"GetNodeFailed: {str(e)}")
            return []
    
    def get_entities_by_type(
        self, 
        graph_id: str, 
        entity_type: str
    ) -> List[NodeInfo]:
        """
        byTypeGet
        
        Args:
            graph_id: GraphID
            entity_type: Entity types(such as Student, PublicFigure etc.)
            
        Returns:
            matchType's List
        """
        logger.info(f"GetTypeas {entity_type} 's ...")
        
        all_nodes = self.get_all_nodes(graph_id)
        
        filtered = []
        for node in all_nodes:
            # ChecklabelsiswhetherContainsSpecifiedType
            if entity_type in node.labels:
                filtered.append(node)
        
        logger.info(f"to {len(filtered)}  {entity_type} Type's ")
        return filtered
    
    def get_entity_summary(
        self, 
        graph_id: str, 
        entity_name: str
    ) -> Dict[str, Any]:
        """
        GetSpecified's Relationship summary
        
        Searchwith's AllInformation, GenerateSummary
        
        Args:
            graph_id: GraphID
            entity_name: Entity name
            
        Returns:
            Entity summaryInformation
        """
        logger.info(f"Get {entity_name} 's Relationship summary...")
        
        # firstSearch's Information
        search_result = self.search_graph(
            graph_id=graph_id,
            query=entity_name,
            limit=20
        )
        
        # try toinAllNodeinto
        all_nodes = self.get_all_nodes(graph_id)
        entity_node = None
        for node in all_nodes:
            if node.name.lower() == entity_name.lower():
                entity_node = node
                break
        
        related_edges = []
        if entity_node:
            # graph_idParameters
            related_edges = self.get_node_edges(graph_id, entity_node.uuid)
        
        return {
            "entity_name": entity_name,
            "entity_info": entity_node.to_dict() if entity_node else None,
            "related_facts": search_result.facts,
            "related_edges": [e.to_dict() for e in related_edges],
            "total_relations": len(related_edges)
        }
    
    def get_graph_statistics(self, graph_id: str) -> Dict[str, Any]:
        """
        GetGraph's Statistics
        
        Args:
            graph_id: GraphID
            
        Returns:
            Statistics
        """
        logger.info(f"GetGraph {graph_id} 's Statistics...")
        
        nodes = self.get_all_nodes(graph_id)
        edges = self.get_all_edges(graph_id)
        
        # StatisticsEntity types
        entity_types = {}
        for node in nodes:
            for label in node.labels:
                if label not in ["Entity", "Node"]:
                    entity_types[label] = entity_types.get(label, 0) + 1
        
        # StatisticsRelationship types
        relation_types = {}
        for edge in edges:
            relation_types[edge.name] = relation_types.get(edge.name, 0) + 1
        
        return {
            "graph_id": graph_id,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entity_types": entity_types,
            "relation_types": relation_types
        }
    
    def get_simulation_context(
        self, 
        graph_id: str,
        simulation_requirement: str,
        limit: int = 30
    ) -> Dict[str, Any]:
        """
        GetSimulated's onunderInformation
        
        SearchwithSimulation requirement's AllInformation
        
        Args:
            graph_id: GraphID
            simulation_requirement: Simulation requirementDescription
            limit: each Information's CountLimit
            
        Returns:
            SimulatedonunderInformation
        """
        logger.info(f"GetSimulatedonunder: {simulation_requirement[:50]}...")
        
        # SearchwithSimulation requirement's Information
        search_result = self.search_graph(
            graph_id=graph_id,
            query=simulation_requirement,
            limit=limit
        )
        
        # GetGraph statistics
        stats = self.get_graph_statistics(graph_id)
        
        # GetAllNode
        all_nodes = self.get_all_nodes(graph_id)
        
        # FilterhaveType's (EntityNode)
        entities = []
        for node in all_nodes:
            custom_labels = [l for l in node.labels if l not in ["Entity", "Node"]]
            if custom_labels:
                entities.append({
                    "name": node.name,
                    "type": custom_labels[0],
                    "summary": node.summary
                })
        
        return {
            "simulation_requirement": simulation_requirement,
            "related_facts": search_result.facts,
            "graph_statistics": stats,
            "entities": entities[:limit],  # LimitCount
            "total_entities": len(entities)
        }
    
    # ========== CoreRetrieve(after) ==========
    
    def insight_forge(
        self,
        graph_id: str,
        query: str,
        simulation_requirement: str,
        report_context: str = "",
        max_sub_queries: int = 5
    ) -> InsightForgeResult:
        """
        [InsightForge - Deep insightRetrieve]
        
        's RetrieveFunction, AutomaticDecomposeQuestionDimensionRetrieve: 
        1. UsesLLMwillQuestionDecomposeasMultipleSub-queries
        2. forEachSub-queriesSemantic search
        3. ExtractGetDetailed information
        4. Relationship chains
        5. IntegrateAllResult, GenerateDeep insight
        
        Args:
            graph_id: GraphID
            query: forQuestion
            simulation_requirement: Simulation requirementDescription
            report_context: Report context(optional, foratprecise's Sub-queriesGenerate)
            max_sub_queries: MaxSub-queriesCount
            
        Returns:
            InsightForgeResult: Deep insightRetrieveResult
        """
        logger.info(f"InsightForge Deep insightRetrieve: {query[:50]}...")
        
        result = InsightForgeResult(
            query=query,
            simulation_requirement=simulation_requirement,
            sub_queries=[]
        )
        
        # Step 1: UsesLLMGenerateSub-queries
        sub_queries = self._generate_sub_queries(
            query=query,
            simulation_requirement=simulation_requirement,
            report_context=report_context,
            max_queries=max_sub_queries
        )
        result.sub_queries = sub_queries
        logger.info(f"Generate {len(sub_queries)} Sub-queries")
        
        # Step 2: forEachSub-queriesSemantic search
        all_facts = []
        all_edges = []
        seen_facts = set()
        
        for sub_query in sub_queries:
            search_result = self.search_graph(
                graph_id=graph_id,
                query=sub_query,
                limit=15,
                scope="edges"
            )
            
            for fact in search_result.facts:
                if fact not in seen_facts:
                    all_facts.append(fact)
                    seen_facts.add(fact)
            
            all_edges.extend(search_result.edges)
        
        # fororiginalQuestionalsoSearch
        main_search = self.search_graph(
            graph_id=graph_id,
            query=query,
            limit=20,
            scope="edges"
        )
        for fact in main_search.facts:
            if fact not in seen_facts:
                all_facts.append(fact)
                seen_facts.add(fact)
        
        result.semantic_facts = all_facts
        result.total_facts = len(all_facts)
        
        # Step 3: frominExtractUUID, Getthis's Information(notGetAllNode)
        entity_uuids = set()
        for edge_data in all_edges:
            if isinstance(edge_data, dict):
                source_uuid = edge_data.get('source_node_uuid', '')
                target_uuid = edge_data.get('target_node_uuid', '')
                if source_uuid:
                    entity_uuids.add(source_uuid)
                if target_uuid:
                    entity_uuids.add(target_uuid)
        
        # GetAll's (notLimitCount, Output)
        entity_insights = []
        node_map = {}  # foratafterRelationship chainsBuild
        
        for uuid in list(entity_uuids):  # ProcessAll, nottruncate
            if not uuid:
                continue
            try:
                # GetEachNode's Information
                node = self.get_node_detail(uuid)
                if node:
                    node_map[uuid] = node
                    entity_type = next((l for l in node.labels if l not in ["Entity", "Node"]), "")
                    
                    # Get's Allfacts(nottruncate)
                    related_facts = [
                        f for f in all_facts 
                        if node.name.lower() in f.lower()
                    ]
                    
                    entity_insights.append({
                        "uuid": node.uuid,
                        "name": node.name,
                        "type": entity_type,
                        "summary": node.summary,
                        "related_facts": related_facts  # Output, nottruncate
                    })
            except Exception as e:
                logger.debug(f"GetNode {uuid} Failed: {e}")
                continue
        
        result.entity_insights = entity_insights
        result.total_entities = len(entity_insights)
        
        # Step 4: BuildAllRelationship chains(notLimitCount)
        relationship_chains = []
        for edge_data in all_edges:  # ProcessAll, nottruncate
            if isinstance(edge_data, dict):
                source_uuid = edge_data.get('source_node_uuid', '')
                target_uuid = edge_data.get('target_node_uuid', '')
                relation_name = edge_data.get('name', '')
                
                source_name = node_map.get(source_uuid, NodeInfo('', '', [], '', {})).name or source_uuid[:8]
                target_name = node_map.get(target_uuid, NodeInfo('', '', [], '', {})).name or target_uuid[:8]
                
                chain = f"{source_name} --[{relation_name}]--> {target_name}"
                if chain not in relationship_chains:
                    relationship_chains.append(chain)
        
        result.relationship_chains = relationship_chains
        result.total_relationships = len(relationship_chains)
        
        logger.info(f"InsightForgeCompleted: {result.total_facts}facts, {result.total_entities}, {result.total_relationships}Relationship")
        return result
    
    def _generate_sub_queries(
        self,
        query: str,
        simulation_requirement: str,
        report_context: str = "",
        max_queries: int = 5
    ) -> List[str]:
        """
        UsesLLMGenerateSub-queries
        
        willcomplexQuestionDecomposeasMultipleCanIndependentRetrieve's Sub-queries
        """
        system_prompt = """youisProfessional's QuestionAnalysis. you's TaskiswillcomplexQuestionDecomposeasMultipleCaninSimulatedinIndependent's Sub-queries. 

need: 
1. EachSub-queriesShouldsufficientspecific, CaninSimulatedinto's Agentas or 
2. Sub-queriesShouldcoverQuestion's DifferentDimension(such as: who, what, aswhat, how, when, )
3. Sub-queriesShouldwithSimulatedScenario
4. ReturnJSONFormat: {"sub_queries": ["Sub-queries1", "Sub-queries2", ...]}"""

        user_prompt = f"""Simulation requirement: 
{simulation_requirement}

{f"Report context: {report_context[:500]}" if report_context else ""}

willwithunderQuestionDecomposeas{max_queries}Sub-queries: 
{query}

ReturnJSONFormat's Sub-queriesList. """

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            sub_queries = response.get("sub_queries", [])
            # EnsureisList
            return [str(sq) for sq in sub_queries[:max_queries]]
            
        except Exception as e:
            logger.warning(f"GenerateSub-queriesFailed: {str(e)}, UsesDefaultSub-queries")
            # fallback: ReturnatQuestion's 
            return [
                query,
                f"{query} 's Mainwith",
                f"{query} 's  and ",
                f"{query} 's "
            ][:max_queries]
    
    def panorama_search(
        self,
        graph_id: str,
        query: str,
        include_expired: bool = True,
        limit: int = 50
    ) -> PanoramaResult:
        """
        [PanoramaSearch - Broad search]
        
        Get, AllContent and /Information: 
        1. GetAllNode
        2. GetAll(Expired/'s )
        3. CurrentActive and Information
        
        thisforatNeed, 's Scenario. 
        
        Args:
            graph_id: GraphID
            query: Search query(forat)
            include_expired: iswhetherContainsContent(DefaultTrue)
            limit: ReturnResultCountLimit
            
        Returns:
            PanoramaResult: Search results
        """
        logger.info(f"PanoramaSearch Broad search: {query[:50]}...")
        
        result = PanoramaResult(query=query)
        
        # GetAllNode
        all_nodes = self.get_all_nodes(graph_id)
        node_map = {n.uuid: n for n in all_nodes}
        result.all_nodes = all_nodes
        result.total_nodes = len(all_nodes)
        
        # GetAll(ContainsTime information)
        all_edges = self.get_all_edges(graph_id, include_temporal=True)
        result.all_edges = all_edges
        result.total_edges = len(all_edges)
        
        # facts
        active_facts = []
        historical_facts = []
        
        for edge in all_edges:
            if not edge.fact:
                continue
            
            # asfactsEntity name
            source_name = node_map.get(edge.source_node_uuid, NodeInfo('', '', [], '', {})).name or edge.source_node_uuid[:8]
            target_name = node_map.get(edge.target_node_uuid, NodeInfo('', '', [], '', {})).name or edge.target_node_uuid[:8]
            
            # Determineiswhether/
            is_historical = edge.is_expired or edge.is_invalid
            
            if is_historical:
                # /Expired facts, TimeMark
                valid_at = edge.valid_at or "Unknown"
                invalid_at = edge.invalid_at or edge.expired_at or "Unknown"
                fact_with_time = f"[{valid_at} - {invalid_at}] {edge.fact}"
                historical_facts.append(fact_with_time)
            else:
                # CurrentActive facts
                active_facts.append(edge.fact)
        
        # atQuery
        query_lower = query.lower()
        keywords = [w.strip() for w in query_lower.replace(',', ' ').replace(', ', ' ').split() if len(w.strip()) > 1]
        
        def relevance_score(fact: str) -> int:
            fact_lower = fact.lower()
            score = 0
            if query_lower in fact_lower:
                score += 100
            for kw in keywords:
                if kw in fact_lower:
                    score += 10
            return score
        
        # LimitCount
        active_facts.sort(key=relevance_score, reverse=True)
        historical_facts.sort(key=relevance_score, reverse=True)
        
        result.active_facts = active_facts[:limit]
        result.historical_facts = historical_facts[:limit] if include_expired else []
        result.active_count = len(active_facts)
        result.historical_count = len(historical_facts)
        
        logger.info(f"PanoramaSearchCompleted: {result.active_count}Active, {result.historical_count}")
        return result
    
    def quick_search(
        self,
        graph_id: str,
        query: str,
        limit: int = 10
    ) -> SearchResult:
        """
        [QuickSearch - Search]
        
        , 's Retrieve: 
        1. directly forZepSemantic search
        2. Return's Result
        3. forat, directly 's Retrieve
        
        Args:
            graph_id: GraphID
            query: Search query
            limit: ReturnResultCount
            
        Returns:
            SearchResult: Search results
        """
        logger.info(f"QuickSearch Search: {query[:50]}...")
        
        # directly forhave's search_graphMethod
        result = self.search_graph(
            graph_id=graph_id,
            query=query,
            limit=limit,
            scope="edges"
        )
        
        logger.info(f"QuickSearchCompleted: {result.total_count}Result")
        return result
    
    def interview_agents(
        self,
        simulation_id: str,
        interview_requirement: str,
        simulation_requirement: str = "",
        max_agents: int = 5,
        custom_questions: List[str] = None
    ) -> InterviewResult:
        """
        [InterviewAgents - Deep interview]
        
        forReal's OASISInterviewAPI, InterviewSimulatedinCurrentlyRun's Agent: 
        1. AutomaticReadPersona file, AllSimulatedAgent
        2. UsesLLMAnalysisInterview requirement, Intelligently select's Agent
        3. UsesLLMGenerateInterview questions
        4. for /api/simulation/interview/batch APIRealInterview(DualPlatformInterview)
        5. IntegrateAllInterview results, GenerateInterview report
        
        [need]canNeedSimulation environmentatRun state(OASISnotClose)
        
        [UsesScenario]
        - NeedfromDifferentRolePerspective
        - Needcollectmultiple-partyOpinion and Viewpoint
        - NeedGetSimulatedAgent's RealResponse(LLMSimulated)
        
        Args:
            simulation_id: SimulatedID(foratPersona file and forInterviewAPI)
            interview_requirement: Interview requirementDescription(, such as"for's ")
            simulation_requirement: Simulation requirement(optional)
            max_agents: Interview's AgentCount
            custom_questions: CustomInterview questions(optional, ifnotprovides thenAuto-generate)
            
        Returns:
            InterviewResult: Interview results
        """
        from .simulation_runner import SimulationRunner
        
        logger.info(f"InterviewAgents Deep interview(RealAPI): {interview_requirement[:50]}...")
        
        result = InterviewResult(
            interview_topic=interview_requirement,
            interview_questions=custom_questions or []
        )
        
        # Step 1: ReadPersona file
        profiles = self._load_agent_profiles(simulation_id)
        
        if not profiles:
            logger.warning(f"nottoSimulated {simulation_id} 's Persona file")
            result.summary = "nottocanInterview's AgentPersona file"
            return result
        
        result.total_agents = len(profiles)
        logger.info(f"Loadto {len(profiles)} AgentPersona")
        
        # Step 2: UsesLLMSelectneedInterview's Agent(Returnagent_idList)
        selected_agents, selected_indices, selection_reasoning = self._select_agents_for_interview(
            profiles=profiles,
            interview_requirement=interview_requirement,
            simulation_requirement=simulation_requirement,
            max_agents=max_agents
        )
        
        result.selected_agents = selected_agents
        result.selection_reasoning = selection_reasoning
        logger.info(f"Select {len(selected_agents)} AgentInterview: {selected_indices}")
        
        # Step 3: GenerateInterview questions(such asnoprovides )
        if not result.interview_questions:
            result.interview_questions = self._generate_interview_questions(
                interview_requirement=interview_requirement,
                simulation_requirement=simulation_requirement,
                selected_agents=selected_agents
            )
            logger.info(f"Generate {len(result.interview_questions)} Interview questions")
        
        # willQuestionmergeasInterviewprompt
        combined_prompt = "\n".join([f"{i+1}. {q}" for i, q in enumerate(result.interview_questions)])
        
        # before, AgentFormat
        INTERVIEW_PROMPT_PREFIX = (
            "You are being interviewed. Please based on your persona, all past memories and actions, "
            "answer the following questions directly in plain text.\n"
            "Response requirements:\n"
            "1. Answer directly in natural language, do not call any tools\n"
            "2. Do not return JSON format or tool call format\n"
            "3. Do not use Markdown headings (e.g. #, ##, ###)\n"
            "4. Answer each question sequentially, start each answer with 'Question X:' (X being the question number)\n"
            "5. Separate answers to each question with blank lines\n"
            "6. Answers should be substantive, at least 2-3 sentences per question\n\n"
        )
        optimized_prompt = f"{INTERVIEW_PROMPT_PREFIX}{combined_prompt}"
        
        # Step 4: forReal's InterviewAPI(notSpecifiedplatform, DefaultDualPlatformInterview)
        try:
            # BuildInterview list(notSpecifiedplatform, DualPlatformInterview)
            interviews_request = []
            for agent_idx in selected_indices:
                interviews_request.append({
                    "agent_id": agent_idx,
                    "prompt": optimized_prompt  # Usesafter's prompt
                    # notSpecifiedplatform, APIwillintwitter and redditPlatformallInterview
                })
            
            logger.info(f"forBatch interviewAPI(DualPlatform): {len(interviews_request)} Agent")
            
            # for SimulationRunner 's Batch interviewMethod(notplatform, DualPlatformInterview)
            api_result = SimulationRunner.interview_agents_batch(
                simulation_id=simulation_id,
                interviews=interviews_request,
                platform=None,  # notSpecifiedplatform, DualPlatformInterview
                timeout=180.0   # DualPlatformNeedTimeout
            )
            
            logger.info(f"InterviewAPIReturn: {api_result.get('interviews_count', 0)} Result, success={api_result.get('success')}")
            
            # CheckAPIforiswhetherSuccessfully
            if not api_result.get("success", False):
                error_msg = api_result.get("error", "Unknown")
                logger.warning(f"InterviewAPIReturnFailed: {error_msg}")
                result.summary = f"InterviewAPIforFailed: {error_msg}. CheckOASISSimulation environmentstatus. "
                return result
            
            # Step 5: ParseAPIReturnResult, BuildAgentInterviewObject
            # DualPlatformModeReturnFormat: {"twitter_0": {...}, "reddit_0": {...}, "twitter_1": {...}, ...}
            api_data = api_result.get("result", {})
            results_dict = api_data.get("results", {}) if isinstance(api_data, dict) else {}
            
            for i, agent_idx in enumerate(selected_indices):
                agent = selected_agents[i]
                agent_name = agent.get("realname", agent.get("username", f"Agent_{agent_idx}"))
                agent_role = agent.get("profession", "Unknown")
                agent_bio = agent.get("bio", "")
                
                # GetAgentinPlatform's Interview results
                twitter_result = results_dict.get(f"twitter_{agent_idx}", {})
                reddit_result = results_dict.get(f"reddit_{agent_idx}", {})
                
                twitter_response = twitter_result.get("response", "")
                reddit_response = reddit_result.get("response", "")

                # Clean upcancan's for JSON wrapped
                twitter_response = self._clean_tool_call_response(twitter_response)
                reddit_response = self._clean_tool_call_response(reddit_response)

                # OutputDualPlatformMark
                twitter_text = twitter_response if twitter_response else "(Platformnot)"
                reddit_text = reddit_response if reddit_response else "(Platformnot)"
                response_text = f"[TwitterPlatformResponse]\n{twitter_text}\n\n[RedditPlatformResponse]\n{reddit_text}"

                # ExtractKey quotes(fromPlatform's Responsein)
                import re
                combined_responses = f"{twitter_response} {reddit_response}"

                # Clean upResponseText: removeMark, number, Markdown etc.
                clean_text = re.sub(r'#{1,6}\s+', '', combined_responses)
                clean_text = re.sub(r'\{[^}]*tool_name[^}]*\}', '', clean_text)
                clean_text = re.sub(r'[*_`|>~\-]{2,}', '', clean_text)
                clean_text = re.sub(r'Question\d+[: :]\s*', '', clean_text)
                clean_text = re.sub(r'[[^]]+]', '', clean_text)

                # Strategy1(): Extract's havesubstantiveContent's 
                sentences = re.split(r'[. ! ? ]', clean_text)
                meaningful = [
                    s.strip() for s in sentences
                    if 20 <= len(s.strip()) <= 150
                    and not re.match(r'^[\s\W, ,; ;: :, ]+', s.strip())
                    and not s.strip().startswith(('{', 'Question'))
                ]
                meaningful.sort(key=len, reverse=True)
                key_quotes = [s + ". " for s in meaningful[:3]]

                # Strategy2(): for's inquotation marks""withinText
                if not key_quotes:
                    paired = re.findall(r'\u201c([^\u201c\u201d]{15,100})\u201d', clean_text)
                    paired += re.findall(r'\u300c([^\u300c\u300d]{15,100})\u300d', clean_text)
                    key_quotes = [q for q in paired if not re.match(r'^[, ,; ;: :, ]', q)][:3]
                
                interview = AgentInterview(
                    agent_name=agent_name,
                    agent_role=agent_role,
                    agent_bio=agent_bio[:1000],  # bioLengthLimit
                    question=combined_prompt,
                    response=response_text,
                    key_quotes=key_quotes[:5]
                )
                result.interviews.append(interview)
            
            result.interviewed_count = len(result.interviews)
            
        except ValueError as e:
            # Simulation environmentnotRun
            logger.warning(f"InterviewAPIforFailed(notRun? ): {e}")
            result.summary = f"InterviewFailed: {str(e)}. Simulation environmentcancanalreadyClose, EnsureOASISCurrentlyRun. "
            return result
        except Exception as e:
            logger.error(f"InterviewAPIfor: {e}")
            import traceback
            logger.error(traceback.format_exc())
            result.summary = f"Interview: {str(e)}"
            return result
        
        # Step 6: GenerateInterview summary
        if result.interviews:
            result.summary = self._generate_interview_summary(
                interviews=result.interviews,
                interview_requirement=interview_requirement
            )
        
        logger.info(f"InterviewAgentsCompleted: Interview {result.interviewed_count} Agent(DualPlatform)")
        return result
    
    @staticmethod
    def _clean_tool_call_response(response: str) -> str:
        """Clean up Agent in's  JSON forwrapped, ExtractContent"""
        if not response or not response.strip().startswith('{'):
            return response
        text = response.strip()
        if 'tool_name' not in text[:80]:
            return response
        import re as _re
        try:
            data = json.loads(text)
            if isinstance(data, dict) and 'arguments' in data:
                for key in ('content', 'text', 'body', 'message', 'reply'):
                    if key in data['arguments']:
                        return str(data['arguments'][key])
        except (json.JSONDecodeError, KeyError, TypeError):
            match = _re.search(r'"content"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
            if match:
                return match.group(1).replace('\\n', '\n').replace('\\"', '"')
        return response

    def _load_agent_profiles(self, simulation_id: str) -> List[Dict[str, Any]]:
        """LoadSimulated's AgentPersona file"""
        import os
        import csv
        
        # BuildPersonaFile path
        sim_dir = os.path.join(
            os.path.dirname(__file__), 
            f'../../uploads/simulations/{simulation_id}'
        )
        
        profiles = []
        
        # firsttry toReadReddit JSONFormat
        reddit_profile_path = os.path.join(sim_dir, "reddit_profiles.json")
        if os.path.exists(reddit_profile_path):
            try:
                with open(reddit_profile_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                logger.info(f"from reddit_profiles.json Load {len(profiles)} Persona")
                return profiles
            except Exception as e:
                logger.warning(f"Read reddit_profiles.json Failed: {e}")
        
        # try toReadTwitter CSVFormat
        twitter_profile_path = os.path.join(sim_dir, "twitter_profiles.csv")
        if os.path.exists(twitter_profile_path):
            try:
                with open(twitter_profile_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # CSVFormatConvertasFormat
                        profiles.append({
                            "realname": row.get("name", ""),
                            "username": row.get("username", ""),
                            "bio": row.get("description", ""),
                            "persona": row.get("user_char", ""),
                            "profession": "Unknown"
                        })
                logger.info(f"from twitter_profiles.csv Load {len(profiles)} Persona")
                return profiles
            except Exception as e:
                logger.warning(f"Read twitter_profiles.csv Failed: {e}")
        
        return profiles
    
    def _select_agents_for_interview(
        self,
        profiles: List[Dict[str, Any]],
        interview_requirement: str,
        simulation_requirement: str,
        max_agents: int
    ) -> tuple:
        """
        UsesLLMSelectneedInterview's Agent
        
        Returns:
            tuple: (selected_agents, selected_indices, reasoning)
                - selected_agents: inAgent's InformationList
                - selected_indices: inAgent's IndexList(foratAPIfor)
                - reasoning: Select
        """
        
        # BuildAgentSummaryList
        agent_summaries = []
        for i, profile in enumerate(profiles):
            summary = {
                "index": i,
                "name": profile.get("realname", profile.get("username", f"Agent_{i}")),
                "profession": profile.get("profession", "Unknown"),
                "bio": profile.get("bio", "")[:200],
                "interested_topics": profile.get("interested_topics", [])
            }
            agent_summaries.append(summary)
        
        system_prompt = """youisProfessional's Interview. you's TaskisInterview requirement, fromSimulatedAgentListinSelectInterview's Object. 

Select: 
1. Agent's /ProfessionwithInterview topic
2. Agentcancanhave or havevalue's Viewpoint
3. Select's Perspective(such as: Supports, for, in, Professionaletc.)
4. firstSelectwithdirectly 's Role

ReturnJSONFormat: 
{
    "selected_indices": [inAgent's IndexList],
    "reasoning": "SelectDescription"
}"""

        user_prompt = f"""Interview requirement: 
{interview_requirement}

Simulated: 
{simulation_requirement if simulation_requirement else "Not provided"}

optional's AgentList(total{len(agent_summaries)}): 
{json.dumps(agent_summaries, ensure_ascii=False, indent=2)}

Select{max_agents}Interview's Agent, DescriptionSelect. """

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            selected_indices = response.get("selected_indices", [])[:max_agents]
            reasoning = response.get("reasoning", "atAuto-select")
            
            # Getin's AgentInformation
            selected_agents = []
            valid_indices = []
            for idx in selected_indices:
                if 0 <= idx < len(profiles):
                    selected_agents.append(profiles[idx])
                    valid_indices.append(idx)
            
            return selected_agents, valid_indices, reasoning
            
        except Exception as e:
            logger.warning(f"LLMSelectAgentFailed, UsesDefaultSelect: {e}")
            # fallback: SelectbeforeN
            selected = profiles[:max_agents]
            indices = list(range(min(max_agents, len(profiles))))
            return selected, indices, "UsesDefaultSelectStrategy"
    
    def _generate_interview_questions(
        self,
        interview_requirement: str,
        simulation_requirement: str,
        selected_agents: List[Dict[str, Any]]
    ) -> List[str]:
        """UsesLLMGenerateInterview questions"""
        
        agent_roles = [a.get("profession", "Unknown") for a in selected_agents]
        
        system_prompt = """youisProfessional's /Interview. Interview requirement, Generate3-5Interview questions. 

Questionneed: 
1. open-endedQuestion, encourageDetailedResponse
2. forDifferentRolecancanhaveDifferentAnswer
3. coverfacts, Viewpoint, feelingsetc.MultipleDimension
4. natural, RealInterview
5. EachQuestioncontrolin50withwithin, Concise
6. directly , notneedContainsDescription or before

ReturnJSONFormat: {"questions": ["Question1", "Question2", ...]}"""

        user_prompt = f"""Interview requirement: {interview_requirement}

Simulated: {simulation_requirement if simulation_requirement else "Not provided"}

InterviewObjectRole: {', '.join(agent_roles)}

Generate3-5Interview questions. """

        try:
            response = self.llm.chat_json(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )
            
            return response.get("questions", [f"at{interview_requirement}, havewhat? "])
            
        except Exception as e:
            logger.warning(f"GenerateInterview questionsFailed: {e}")
            return [
                f"at{interview_requirement}, 's Viewpointiswhat? ",
                "thisfor or 's havewhat? ",
                "asShouldsuch as or thisQuestion? "
            ]
    
    def _generate_interview_summary(
        self,
        interviews: List[AgentInterview],
        interview_requirement: str
    ) -> str:
        """GenerateInterview summary"""
        
        if not interviews:
            return "Not completedInterview"
        
        # collectAllInterviewContent
        interview_texts = []
        for interview in interviews:
            interview_texts.append(f"[{interview.agent_name}({interview.agent_role})]\n{interview.response[:500]}")
        
        system_prompt = """youisProfessional's . interviewees's Response, GenerateInterview summary. 

Summaryneed: 
1. extractper-MainViewpoint
2. Viewpoint's total and disagreement
3. highlighthavevalue's Quote
4. in, notbiased
5. controlin1000within

Format(Must): 
- UsesPlain text, forblank lineseparateDifferentPartial
- Do not use Markdown headings (e.g. #, ##, ###)
- notneedUsesdividers(such as---, ***)
- Citeintervieweesoriginal wordsUsesinquotation marks""
- CanUses**bold**Markword, butnotneedUsesOtherMarkdown"""

        user_prompt = f"""Interview topic: {interview_requirement}

InterviewContent: 
{"".join(interview_texts)}

GenerateInterview summary. """

        try:
            summary = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            return summary
            
        except Exception as e:
            logger.warning(f"GenerateInterview summaryFailed: {e}")
            # fallback: 
            return f"totalInterview{len(interviews)}interviewees, : " + ", ".join([i.agent_name for i in interviews])
