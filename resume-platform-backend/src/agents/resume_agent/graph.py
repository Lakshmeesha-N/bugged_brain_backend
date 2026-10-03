from pathlib import Path
from langgraph.graph import END, StateGraph
from src.agents.resume_agent.nodes import generate, load_template, validate
from src.agents.resume_agent.state import ResumeState


def should_retry(state: ResumeState) -> str:
    if state.get("validation_error") is not None and state.get("attempts", 0) < 2:
        return "generate"
    return END


def create_resume_graph():
    builder = StateGraph(ResumeState)

    builder.add_node("load_template", load_template)
    builder.add_node("generate", generate)
    builder.add_node("validate", validate)

    builder.set_entry_point("load_template")
    builder.add_edge("load_template", "generate")
    builder.add_edge("generate", "validate")

    builder.add_conditional_edges(
        "validate",
        should_retry,
        {
            "generate": "generate",
            END: END,
        }
    )

    return builder.compile()


graph = create_resume_graph()


async def run_resume_agent(
    template_id: str,
    profile: dict,
    extra_info: str | None = None,
    answers: list[dict] | None = None
) -> dict:
    initial_state: ResumeState = {
        "template_id": template_id,
        "profile": profile,
        "extra_info": extra_info,
        "answers": answers or [],
        "attempts": 0,
    }
    final_state = await graph.ainvoke(initial_state)
    return final_state["result"]


def main():
    """Generates the image of the LangGraph state graph and saves it in the project root."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    output_path = root_dir / "resume_agent_graph.png"
    
    try:
        # Generate mermaid png bytes
        image_bytes = graph.get_graph().draw_mermaid_png()
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"Resume agent graph image successfully saved to: {output_path}")
    except Exception as e:
        # Fallback to ascii/text representation if rendering dependencies (e.g. mermaid API) fail
        print(f"Could not render PNG directly ({e}). Generating mermaid ascii...")
        ascii_graph = graph.get_graph().draw_ascii()
        print(ascii_graph)


if __name__ == "__main__":
    main()
