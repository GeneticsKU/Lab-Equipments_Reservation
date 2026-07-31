# Lecturer Lab Dropdown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace user-entered affiliation text with a dropdown sourced from approved lecturer sponsor affiliations.

**Architecture:** A pure helper in `bridge/ui_access_requests.py` derives sorted unique options from existing sponsor records. Both registration and profile completion reuse it, while existing server-side validation remains unchanged.

**Tech Stack:** Python, Streamlit, pytest

---

### Task 1: Derive Lecturer Lab Options

**Files:**
- Modify: `bridge/ui_access_requests.py`
- Test: `tests/test_bridge_access_requests.py`

- [ ] **Step 1: Write the failing helper test**

Import `lecturer_lab_options` and add:

```python
def test_lecturer_lab_options_returns_unique_approved_lecturer_affiliations() -> None:
    lecturer = BridgeUser(
        id="lecturer-1",
        email="one@ku.th",
        user_category="Lecturer",
        affiliation=" 4511 ",
        approval_state="approved",
        is_sponsor=True,
    )
    duplicate = replace(lecturer, id="lecturer-2", email="two@ku.th")
    other_lab = replace(lecturer, id="lecturer-3", email="three@ku.th", affiliation="4607")
    admin = replace(lecturer, id="admin", email="admin@ku.th", affiliation="4503", is_admin=True)
    inactive = replace(lecturer, id="inactive", email="inactive@ku.th", affiliation="4612", approval_state="denied")

    assert lecturer_lab_options([other_lab, duplicate, admin, inactive, lecturer]) == ["4511", "4607"]
```

- [ ] **Step 2: Run the test and verify failure**

Run:

```bash
.venv/bin/python -m pytest tests/test_bridge_access_requests.py::test_lecturer_lab_options_returns_unique_approved_lecturer_affiliations -q
```

Expected: import failure because `lecturer_lab_options` does not exist.

- [ ] **Step 3: Implement the minimal helper**

Add to `bridge/ui_access_requests.py`:

```python
def lecturer_lab_options(users):
    return sorted(
        {
            user.affiliation.strip()
            for user in users
            if user.user_category == "Lecturer"
            and user.approval_state == "approved"
            and user.is_sponsor
            and not user.is_admin
            and (user.affiliation or "").strip()
        },
        key=str.casefold,
    )
```

- [ ] **Step 4: Run the helper test**

Run the targeted pytest command again.

Expected: `1 passed`.

### Task 2: Replace Both Free-Text Inputs

**Files:**
- Modify: `bridge/ui_access_requests.py`
- Modify: `app.py`

- [ ] **Step 1: Update registration**

After loading sponsors, calculate:

```python
lab_options = lecturer_lab_options(sponsors)
```

Show an error when the list is empty. Otherwise replace the affiliation `st.text_input` with:

```python
affiliation = st.selectbox("Lab number or affiliation", lab_options)
```

- [ ] **Step 2: Update profile completion**

Import `lecturer_lab_options`, calculate options from the loaded sponsors, and replace the affiliation text input with:

```python
affiliation = st.selectbox(
    "Lab number or affiliation",
    lab_options,
    index=lab_options.index(bridge_user.affiliation)
    if bridge_user.affiliation in lab_options
    else 0,
)
```

If the option list is empty, show an administrator-contact error and do not render the form.

- [ ] **Step 3: Verify the complete change**

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m py_compile app.py bridge/ui_access_requests.py
git diff --check
```

Expected: all tests pass, compilation succeeds, and no diff errors are reported.

- [ ] **Step 4: Commit and deploy**

```bash
git add app.py bridge/ui_access_requests.py tests/test_bridge_access_requests.py
git commit -m "feat: use lecturer labs for affiliation choices"
git fetch origin main
git rebase origin/main
git push origin HEAD:main
```
