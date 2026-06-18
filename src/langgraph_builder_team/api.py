from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .graph import run_build
from .models import BuildRequest, BuildResponse
from .settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """
    <!doctype html>
    <html lang="de">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>LangGraph Builder Team</title>
        <style>
          body { font-family: system-ui, sans-serif; margin: 2rem; max-width: 980px; }
          textarea { width: 100%; min-height: 160px; }
          button { padding: .7rem 1rem; margin-top: .75rem; }
          pre { background: #111827; color: #e5e7eb; padding: 1rem; overflow:auto; }
        </style>
      </head>
      <body>
        <h1>LangGraph Builder Team</h1>
        <textarea id="request">Baue einen LangGraph Agent Workflow mit Planner,
Builder, Tester, Reviewer und Deployment.</textarea>
        <br />
        <button onclick="build()">Build starten</button>
        <pre id="out">Bereit.</pre>
        <script>
          async function build() {
            const out = document.getElementById('out');
            out.textContent = 'Laeuft...';
            const response = await fetch('/build', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({user_request: document.getElementById('request').value})
            });
            out.textContent = JSON.stringify(await response.json(), null, 2);
          }
        </script>
      </body>
    </html>
    """


@app.post("/build", response_model=BuildResponse)
def build(request: BuildRequest) -> BuildResponse:
    state = run_build(request.user_request, request.project_id)
    return BuildResponse(
        project_id=state.project_id,
        status=state.status,
        quality_score=state.quality_score,
        plan=state.plan,
        artifacts=state.generated_artifacts,
        review_feedback=state.review_feedback,
        verification_result=state.verification_result,
        deployment_instructions=state.deployment_instructions,
    )
