# Lecturer Lab Dropdown

## Goal

Users must choose a lab number or affiliation from the current lecturer directory instead of entering free text.

## Behavior

- Build the available lab list from distinct, non-empty `affiliation` values belonging to approved lecturer sponsors.
- Sort and deduplicate the values before display.
- Use the same list for new access requests and approved-user profile completion.
- Preserve existing completed profiles; this change only controls future form submissions.
- If no lecturer lab values are available, show an administrator-contact error and do not allow submission.

## Implementation

- Add one small tested helper in `bridge/ui_access_requests.py` that derives lab options from sponsor records.
- Replace the registration affiliation text field with a Streamlit select box.
- Reuse the helper for the profile-completion select box in `app.py`.
- Keep server-side required-affiliation validation unchanged.

## Verification

- Test filtering, deduplication, and sorting of lecturer lab values.
- Run the full test suite.
- Verify both forms contain the dropdown and no free-text affiliation input.
