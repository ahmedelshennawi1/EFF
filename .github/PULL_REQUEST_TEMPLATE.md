## Description
Brief summary of the changes introduced in this PR.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New machinery profile / sector data
- [ ] New feature / enhancement in engine or UI
- [ ] Documentation update
- [ ] CI / GitHub workflow improvement

## Quality Checklist
- [ ] All 63 tests pass: `python tests/test_eff.py`
- [ ] Machinery library validates: `python cli.py --check-library`
- [ ] No third-party dependencies added to core `eff/` package (pure Python stdlib)
- [ ] Missing data rules honored (no 0-filling unmeasured values)
- [ ] Overrides act only as floors, not demotions
- [ ] Documentation and booklets updated where applicable
