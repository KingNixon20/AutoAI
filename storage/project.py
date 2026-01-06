import pathlib
from .workflow import Workflow


class Project:
    def __init__(self, path: pathlib.Path):
        self.path = pathlib.Path(path)
        self.name = self.path.name
        self.workflows_dir = self.path / "workflows"
        self.workflows_dir.mkdir(parents=True, exist_ok=True)

    def list_workflows(self):
        out = []
        for f in self.workflows_dir.glob("*.yaml"):
            try:
                wf = Workflow.load(f)
                out.append((f, wf))
            except Exception:
                continue
        return out

    def save_workflow(self, workflow: Workflow):
        path = self.workflows_dir / f"{workflow.name}.yaml"
        workflow.save(path)
        return path
