"""MLflow ResponsesAgent implementation for read-only Naturapet impact analysis."""

import logging
from typing import AsyncGenerator
from uuid import uuid4

import mlflow
from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from agents.tracing import set_trace_processors
from databricks.sdk import WorkspaceClient
from databricks_openai import AsyncDatabricksOpenAI
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    create_text_output_item,
)

from agent_server.config import RepositoryConfig
from agent_server.prompts import IMPACT_ANALYZER_INSTRUCTIONS
from agent_server.repository.client import DatabricksRepositoryClient
from agent_server.repository.tools import AnalysisRunContext, REPOSITORY_TOOLS
from agent_server.schemas import (
    ImpactAnalysisDraft,
    ImpactAnalysisResult,
    finalize_analysis,
)
from agent_server.utils import get_session_id


logger = logging.getLogger(__name__)

# This client uses the Databricks App service principal credentials in deployment.
set_default_openai_client(AsyncDatabricksOpenAI())
set_default_openai_api("chat_completions")
set_trace_processors([])
mlflow.openai.autolog()
logging.getLogger("mlflow.utils.autologging_utils").setLevel(logging.ERROR)


def create_agent() -> Agent[AnalysisRunContext]:
    """Construct the fixed-schema read-only impact analyzer."""
    return Agent[AnalysisRunContext](
        name="Naturapet Impact Analyzer",
        instructions=IMPACT_ANALYZER_INSTRUCTIONS,
        model="databricks-gpt-5-2",
        tools=REPOSITORY_TOOLS,
        output_type=ImpactAnalysisDraft,
    )


async def run_analysis(request: ResponsesAgentRequest) -> ImpactAnalysisResult:
    """Verify repository identity before running one evidence-based analysis."""
    config = RepositoryConfig.from_environment()
    repository = DatabricksRepositoryClient(WorkspaceClient(), config)
    verified_context = repository.get_context()
    run_context = AnalysisRunContext(repository=repository, config=config)
    messages = [item.model_dump() for item in request.input]
    result = await Runner.run(create_agent(), messages, context=run_context)
    draft = ImpactAnalysisDraft.model_validate(result.final_output)
    return finalize_analysis(draft, verified_context)


def build_response(result: ImpactAnalysisResult) -> ResponsesAgentResponse:
    """Expose canonical JSON to machines and its derived Markdown to humans."""
    message = create_text_output_item(result.human_report_markdown, str(uuid4()))
    message["status"] = "completed"
    return ResponsesAgentResponse(
        output=[message],
        custom_outputs={"analysis": result.model_dump(mode="json")},
        status="completed",
    )


@invoke()
async def invoke_handler(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    """Return a canonical impact analysis through the ResponsesAgent endpoint."""
    if session_id := get_session_id(request):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})
    return build_response(await run_analysis(request))


@stream()
async def stream_handler(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """Emit the same complete canonical response without streaming draft JSON tokens."""
    if session_id := get_session_id(request):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session_id})
    response = build_response(await run_analysis(request))
    yield ResponsesAgentStreamEvent(
        type="response.output_item.done",
        item=response.output[0].model_dump(mode="json"),
        output_index=0,
    )
    yield ResponsesAgentStreamEvent(
        type="response.completed",
        response=response.model_dump(mode="json"),
    )
