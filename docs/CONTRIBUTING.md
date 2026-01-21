# Contributing to CEP Proprietary Machine

Thank you for your interest in contributing! This guide will help you get started.

## Development Philosophy

> **WE NEVER MAP IN TIMEFRAMES, WE MAP IN STEPS**

We believe in:
- Clear, incremental progress
- Well-defined steps
- Quality over speed
- Discipline in execution

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
git clone https://github.com/YOUR_USERNAME/myMachine.git
cd myMachine
```

### 2. Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cep_machine

# Run specific test
pytest tests/test_layer1.py -v
```

## Code Standards

### Python Style

We follow PEP 8 with these modifications:

```python
# Good
class MyLayer:
    """Layer description."""
    
    def __init__(self, param: str):
        self.param = param
    
    async def process(self) -> Result:
        """Process data."""
        return await self._do_work()
    
    async def _do_work(self) -> Result:
        """Internal work."""
        # Implementation
        pass

# Bad
class mylayer:
    def __init__(self, param):
        self.p=param
```

### Type Hints

All functions must have type hints:

```python
from typing import Dict, List, Optional

async def process_data(
    input_data: Dict[str, Any],
    options: Optional[List[str]] = None
) -> Result:
    """Process the input data."""
    pass
```

### Documentation

Every public function needs a docstring:

```python
def calculate_metrics(
    data: List[Dict[str, Any]],
    window_size: int = 30
) -> Metrics:
    """
    Calculate performance metrics.
    
    Args:
        data: List of performance data points
        window_size: Number of days to average
    
    Returns:
        Metrics object with calculated values
    
    Raises:
        ValueError: If data is empty
    """
    pass
```

## Architecture Guidelines

### Layer Structure

Each layer must follow this structure:

```python
# cep_machine/layers/new_layer.py

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

# 1. Data classes
@dataclass
class LayerResult:
    """Result of layer processing."""
    success: bool
    data: Dict[str, Any]
    errors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

# 2. Main engine class
class NewLayerEngine:
    """Layer X: New Layer functionality."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
    
    async def process(self, input_data: Any) -> LayerResult:
        """Main processing method."""
        # Implementation
        pass

# 3. Entry point function
async def run_layer(
    param1: str,
    param2: Optional[int] = None,
    dry_run: bool = True
) -> LayerResult:
    """
    Main entry point for Layer X.
    
    Args:
        param1: Description
        param2: Optional description
    
    Returns:
        LayerResult with processing details
    """
    print(f"\n{'='*60}")
    print(f"[Layer X] NEW LAYER")
    print(f"{'='*60}\n")
    
    engine = NewLayerEngine(dry_run=dry_run)
    result = await engine.process(param1, param2)
    
    print(f"\n[Layer X] ✓ Complete")
    return result

# 4. Exports
__all__ = [
    "LayerResult",
    "NewLayerEngine", 
    "run_layer",
]
```

### Container Integration

Add to appropriate container:

```python
# cep_machine/core/containers.py

class SalesContainer(CEPContainer):
    def record_new_layer_event(self, data: Dict[str, Any]) -> None:
        """Record new layer event."""
        self.record_event("new_layer_processed", data)
        self._update_metrics()
```

## Testing Guidelines

### Test Structure

```python
# tests/test_new_layer.py

import pytest
import asyncio
from cep_machine.layers.new_layer import run_layer, LayerResult

class TestNewLayer:
    """Test Layer X functionality."""
    
    @pytest.fixture
    def test_data(self):
        return {"key": "value"}
    
    @pytest.mark.asyncio
    async def test_basic_processing(self, test_data):
        """Test basic layer processing."""
        result = await run_layer(
            param1="test",
            param2=123,
            dry_run=True
        )
        
        assert isinstance(result, LayerResult)
        assert result.success
        assert "processed" in result.data
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling."""
        result = await run_layer(
            param1="invalid",
            dry_run=True
        )
        
        assert not result.success
        assert len(result.errors) > 0
```

### Test Coverage

- All public functions must be tested
- Test both success and error cases
- Mock external dependencies
- Test async functions properly

### Integration Tests

Add to `tests/test_integration.py`:

```python
async def test_layer_x_integration(self, test_business, system_state):
    """Test Layer X in golden path."""
    result = await run_layer_x(
        param=test_business["name"],
        dry_run=True
    )
    
    assert result.success
    system_state["layer_x_results"].append(result)
    system_state["phi_sync"] += 0.08
```

## Submitting Changes

### 1. Create Branch

```bash
# From main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/new-layer
```

### 2. Make Changes

- Follow code standards
- Add tests
- Update documentation
- Commit frequently

### 3. Test Changes

```bash
# Run all tests
pytest

# Run linting
flake8 cep_machine/
mypy cep_machine/

# Run integration test
python tests/test_integration.py
```

### 4. Commit

```bash
# Stage changes
git add .

# Commit with conventional message
git commit -m "feat(layer-x): Add new layer functionality

- Implement NewLayerEngine class
- Add run_layer entry point
- Include comprehensive tests
- Update documentation

Container: Sales
Φ contribution: +0.08"
```

### 5. Push and PR

```bash
# Push to your fork
git push origin feature/new-layer

# Create Pull Request on GitHub
```

## Pull Request Process

### PR Requirements

1. **Clear title and description**
2. **Tests passing**
3. **Documentation updated**
4. **No breaking changes**
5. **Φ_sync impact documented**

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Φ_sync impact calculated

## Φ_sync Impact
- Base: 0.85
- Added: +0.08
- Expected: 0.93
```

### Review Process

1. **Automated checks** (CI/CD)
2. **Peer review** (1-2 reviewers)
3. **Architecture review** (for major changes)
4. **Final approval** (maintainer)

## Release Process

### Version Bumping

We use semantic versioning:
- **MAJOR**: Breaking changes
- **MINOR**: New features
- **PATCH**: Bug fixes

### Release Steps

1. Update version in `__init__.py`
2. Update CHANGELOG.md
3. Create release tag
4. Deploy to production

## Community

### Getting Help

- GitHub Issues: Report bugs
- GitHub Discussions: Questions
- Discord: Real-time chat

### Code of Conduct

- Be respectful
- Be constructive
- Be inclusive
- Focus on what's best for the community

## Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- Annual contributor awards

## Resources

- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Issue Tracker](https://github.com/stackconsult/myMachine/issues)

---

*Thank you for contributing to the CEP Proprietary Machine!*
