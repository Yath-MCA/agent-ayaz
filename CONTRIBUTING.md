# Contributing to Agent Ayazdy

Thank you for your interest in contributing to Agent Ayazdy! This guide will help you get started.

---

## 🚀 Quick Start for Contributors

### 1. Fork & Clone

```bash
git clone https://github.com/yourusername/agent-ayazdy.git
cd agent-ayazdy
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 4. Run Tests (if available)

```bash
pytest tests/
```

### 5. Run the Agent

```bash
python main.py
```

---

## 📋 Contribution Guidelines

### What We're Looking For

- 🐛 **Bug fixes** — especially edge cases in agent pipeline, approval workflow, or execution service
- ✨ **New features** — plugins, agent modes, monitoring enhancements
- 📚 **Documentation** — tutorials, examples, API guides, plugin development docs
- 🧪 **Tests** — unit tests for agents, services, security modules
- 🎨 **Dashboard improvements** — UI/UX enhancements, new panels, visualizations

### What We're NOT Looking For

- Breaking changes without prior discussion (open an issue first)
- Large refactors without clear motivation
- Dependencies that significantly increase install size
- Features that compromise security or auditability

---

## 🛠 Development Workflow

### Branching Strategy

- `main` — stable, production-ready code
- `feature/your-feature-name` — new features
- `fix/issue-description` — bug fixes
- `docs/topic` — documentation updates

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(agents): add priority queue support
fix(approval): handle timeout edge case in token validation
docs(readme): add plugin development examples
test(validator): add unit tests for policy gate
chore(deps): update pyyaml to 6.0.2
```

**Types:** `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `perf`, `ci`

**Scope:** `agents`, `services`, `security`, `plugins`, `cli`, `dashboard`, `api`, `telegram`, `queue`, `docs`

### Pull Request Process

1. **Open an issue first** (for non-trivial changes) to discuss approach
2. **Create a feature branch** from `main`
3. **Make your changes** with clear, focused commits
4. **Add tests** if applicable (new agents, services, security logic)
5. **Update documentation** (README, CHANGELOG, inline comments)
6. **Run existing tests** to ensure nothing broke
7. **Submit PR** with description linking to the issue

**PR Title Format:**
```
feat(agents): Add priority queue support (#123)
fix(approval): Handle timeout edge case (#124)
docs(readme): Add plugin examples (#125)
```

**PR Description Template:**
```markdown
## Changes
Brief description of what changed and why.

## Related Issue
Fixes #123

## Testing
- [ ] Added unit tests
- [ ] Manually tested with [scenario]
- [ ] Existing tests pass

## Checklist
- [ ] Documentation updated (README, CHANGELOG, inline comments)
- [ ] No breaking changes (or discussed in issue first)
- [ ] Follows project code style
- [ ] Commit messages follow Conventional Commits
```

---

## 🧪 Testing Guidelines

### Running Tests

```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_agents.py

# With coverage
pytest --cov=agents --cov=services tests/
```

### Writing Tests

Place tests in `tests/` directory mirroring source structure:

```
tests/
├── test_agents.py
├── test_services.py
├── test_security.py
└── test_plugins.py
```

**Example test:**

```python
# tests/test_agents.py
import pytest
from agents.planner import PlannerAgent

def test_planner_generates_valid_json():
    planner = PlannerAgent(model="phi3")
    result = planner.plan("List files in current directory")
    assert "steps" in result
    assert isinstance(result["steps"], list)
```

---

## 🔌 Plugin Development

Plugins are the easiest way to extend Agent Ayazdy.

### Plugin Structure

Create a file in `plugins/` (e.g., `plugins/my_plugin.py`):

```python
def register(manager):
    """Called automatically on startup."""
    
    @manager.register("before_plan")
    def on_before_plan(ctx):
        print(f"Planning task: {ctx['task']}")
    
    @manager.register("after_execution")
    def on_after_execution(ctx):
        if ctx["status"] == "failed":
            print(f"Task failed: {ctx['error']}")
```

### Available Hooks

| Hook | When | Context Keys |
|---|---|---|
| `before_plan` | Before planner generates plan | `project`, `task` |
| `after_validation` | After validator approves/rejects | `project`, `task`, `plan`, `approved` |
| `after_execution` | After executor completes | `project`, `task`, `plan`, `status`, `output`, `duration` |
| `on_error` | On any pipeline error | `project`, `task`, `error`, `phase` |

### Example Plugin Ideas

- **Slack notifier** — Send notifications on task completion/failure
- **Metrics exporter** — Export execution metrics to Prometheus
- **Custom validator** — Add project-specific validation rules
- **Auto-retry** — Retry failed tasks with exponential backoff
- **Code formatter** — Auto-format code after successful build
- **Deployment hook** — Trigger deployment after successful test run

---

## 🎨 Dashboard Development

The dashboard is a CDN-based React app (no build step).

### Making Changes

1. Edit `dashboard/js/app.js` (JSX compiled in-browser via Babel)
2. Refresh browser — changes visible immediately
3. No build, no npm install, no bundler

### Adding New Panels

```javascript
function MyNewPanel({ autoRefresh }) {
  const [data, setData] = useState(null);

  const load = useCallback(() => {
    api("/my/new/endpoint").then(setData).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    if (!autoRefresh) return;
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load, autoRefresh]);

  return (
    <Card title="My Panel" action={<RefreshBtn onClick={load} />}>
      {!data && <Spinner />}
      {data && <div>{JSON.stringify(data)}</div>}
    </Card>
  );
}
```

### Dashboard Guidelines

- Keep panels focused (one responsibility each)
- Use `autoRefresh` prop for periodic polling
- Handle loading/error states gracefully
- Use Tailwind utility classes for styling
- Keep bundle size small (avoid heavy dependencies)

---

## 🏗 Architecture Guidelines

### Agent Design Principles

1. **Single Responsibility** — Each agent does one thing well
2. **Immutability** — Auditor writes append-only log (never modifies)
3. **Separation** — Planner generates, Validator approves, Executor runs
4. **Observability** — All actions logged to audit trail

### Adding New Agents

```python
# agents/my_agent.py
class MyAgent:
    def __init__(self, config=None):
        self.config = config or {}
    
    def process(self, context):
        """Process context and return result."""
        # Your logic here
        return {"status": "success", "data": {...}}
```

Register in `main.py`:

```python
from agents.my_agent import MyAgent

# In startup
my_agent = MyAgent(config={"key": "value"})
app.state.my_agent = my_agent
```

### Code Style

- **PEP 8** — Follow Python style guide
- **Type hints** — Use where helpful (function signatures, complex structures)
- **Docstrings** — Required for public functions/classes
- **Comments** — Only when intent isn't obvious from code
- **Error handling** — Fail gracefully, log errors, provide helpful messages

**Example:**

```python
def validate_plan(plan: dict) -> tuple[bool, str]:
    """
    Validate execution plan structure.
    
    Args:
        plan: ExecutionPlan dict with 'steps' and 'risk_score'
    
    Returns:
        (is_valid, error_message) tuple
    """
    if "steps" not in plan:
        return False, "Missing 'steps' field"
    if not isinstance(plan["steps"], list):
        return False, "'steps' must be a list"
    return True, ""
```

---

## 🐛 Reporting Bugs

### Before Submitting

1. **Search existing issues** — your bug may already be reported
2. **Check troubleshooting guide** in README.md
3. **Reproduce on latest version** — update to `main` branch first

### Bug Report Template

```markdown
**Description**
Clear description of the bug.

**Steps to Reproduce**
1. Run `ayazdy health`
2. Execute task X
3. Observe error Y

**Expected Behavior**
What should happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: Windows 10 / macOS 14 / Ubuntu 22.04
- Python version: 3.12.4
- Agent Ayazdy version: commit hash or release tag
- Ollama version: 0.1.25

**Logs**
Paste relevant logs from `logs/agent_audit.log` or console output.

**Additional Context**
Screenshots, `.env` config (redact secrets), etc.
```

---

## 💬 Getting Help

- **Issues** — For bugs, feature requests, questions
- **Discussions** — For general questions, ideas, show-and-tell
- **Security** — Email security issues privately (do not open public issue)

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

## 🙏 Recognition

Contributors will be acknowledged in:
- CHANGELOG.md (for significant features/fixes)
- GitHub contributors page
- Release notes (for major contributions)

Thank you for making Agent Ayazdy better! 🎉
