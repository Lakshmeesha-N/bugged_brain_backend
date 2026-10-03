from langgraph.graph import END, StateGraph
from src.agents.ats_agent.nodes import analyze, validate
from src.agents.ats_agent.state import AtsState


def should_retry(state: AtsState) -> str:
    if state.get("validation_error") is not None and state.get("attempts", 0) < 2:
        return "analyze"
    return END


def create_ats_graph():
    builder = StateGraph(AtsState)

    builder.add_node("analyze", analyze)
    builder.add_node("validate", validate)

    builder.set_entry_point("analyze")
    builder.add_edge("analyze", "validate")

    builder.add_conditional_edges(
        "validate",
        should_retry,
        {
            "analyze": "analyze",
            END: END,
        }
    )

    return builder.compile()


graph = create_ats_graph()


async def run_ats_agent(
    resume_text: str,
    job_title: str | None = None,
    job_description: str | None = None
) -> dict:
    initial_state: AtsState = {
        "resume_text": resume_text,
        "job_title": job_title,
        "job_description": job_description,
        "attempts": 0,
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state["result"]
