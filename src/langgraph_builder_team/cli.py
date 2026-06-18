import argparse
import json

from .graph import run_build


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LangGraph Builder Team workflow.")
    parser.add_argument("request", help="Project request to build")
    parser.add_argument("--project-id", default=None)
    args = parser.parse_args()
    state = run_build(args.request, args.project_id)
    print(json.dumps(state.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
