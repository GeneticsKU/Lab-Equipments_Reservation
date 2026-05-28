from __future__ import annotations

import streamlit as st

from bridge.auth_store import InvalidAccessRequestError
from bridge.emailer import send_sponsor_approval_email
from bridge.ui_auth import render_deployment_banner


APPLICANT_CATEGORIES = [
    "Undergraduate Student",
    "Master Student",
    "PhD Student",
    "Research Assistant",
    "Researcher",
]


def get_approval_request_id() -> str | None:
    query_params = st.query_params
    request_id = query_params.get("approve_request")
    if isinstance(request_id, list):
        return request_id[0] if request_id else None
    return request_id


def render_applicant_pending_access(settings, auth_store, user, logout_callback) -> None:
    render_deployment_banner(settings)
    st.title("Access Pending")
    st.write(f"Signed in as: {user.email}")

    applicant_requests = auth_store.list_applicant_requests(user.id)
    pending_request = next((request for request in applicant_requests if request["status"] == "Pending"), None)

    if pending_request is None:
        sponsors = auth_store.list_sponsors()
        if not sponsors:
            st.error("No sponsors are configured yet. Please contact the administrator.")
        else:
            sponsor_options = {f"{s.full_name or s.email} ({s.email})": s for s in sponsors}
            with st.form("bridge_access_request_form"):
                full_name = st.text_input("Full name", value=user.full_name or "")
                sponsor_label = st.selectbox("Choose sponsor", list(sponsor_options.keys()))
                suggested_category = st.selectbox("Suggested user category", APPLICANT_CATEGORIES)
                affiliation = st.text_input("Lab (Room number) or department affiliation", value=user.affiliation or "")
                submit_request = st.form_submit_button("Submit access request")

            if submit_request:
                selected_sponsor = sponsor_options[sponsor_label]
                try:
                    created_request = auth_store.create_access_request(
                        applicant_user_id=user.id,
                        full_name=full_name.strip(),
                        email=user.email,
                        chosen_sponsor_user_id=selected_sponsor.id,
                        suggested_user_category=suggested_category,
                        affiliation=affiliation.strip(),
                    )
                    send_sponsor_approval_email(settings, selected_sponsor.email, created_request["id"])
                    st.success("Access request submitted. Your sponsor has been emailed.")
                    st.rerun()
                except (InvalidAccessRequestError, ValueError) as exc:
                    st.error(str(exc))
                except Exception as exc:
                    st.error(f"Unable to submit the access request: {exc}")
    else:
        st.info("Your access request is waiting for sponsor approval.")
        st.write(f"Suggested category: {pending_request['suggested_user_category']}")
        st.write(f"Affiliation: {pending_request['affiliation']}")
        st.write(f"Requested at: {pending_request['created_at']}")

    if applicant_requests:
        st.write("### Your access request history")
        for request in applicant_requests:
            st.write(
                f"- {request['status']}: {request['suggested_user_category']} "
                f"({request['affiliation']})"
            )

    if st.button("Logout", key="bridge_pending_logout"):
        logout_callback()
        st.rerun()


def render_sponsor_review(auth_store, reviewer_user) -> None:
    settings = st.session_state.get("bridge_settings")
    if settings is not None:
        render_deployment_banner(settings)
    request_id = get_approval_request_id()
    if not request_id:
        return

    st.write("### Sponsor approval request")
    request_record = auth_store.get_access_request(request_id)
    if request_record is None:
        st.error("This access request was not found.")
        return
    if not reviewer_user.is_admin and request_record["chosen_sponsor_user_id"] != reviewer_user.id:
        st.error("You are not allowed to review this request.")
        return

    applicant = auth_store.repository.get_user_by_id(request_record["applicant_user_id"])
    st.write(f"Applicant: {(applicant.full_name if applicant else None) or 'Unknown applicant'}")
    st.write(f"Applicant email: {(applicant.email if applicant else 'Unknown email')}")
    st.write(f"Suggested category: {request_record['suggested_user_category']}")
    st.write(f"Affiliation: {request_record['affiliation']}")
    st.write(f"Current status: {request_record['status']}")

    if request_record["status"] != "Pending":
        st.info("This request has already been decided.")
        return

    approved_category = st.selectbox(
        "Approved user category",
        APPLICANT_CATEGORIES,
        index=APPLICANT_CATEGORIES.index(request_record["suggested_user_category"])
        if request_record["suggested_user_category"] in APPLICANT_CATEGORIES
        else 0,
        key=f"bridge_sponsor_category_{request_id}",
    )

    approval_col, denial_col = st.columns(2)
    with approval_col:
        if st.button("Approve request", key=f"bridge_approve_{request_id}"):
            try:
                auth_store.approve_access_request(request_id, reviewer_user.id, approved_user_category=approved_category)
                st.success("Access request approved.")
                st.rerun()
            except (InvalidAccessRequestError, PermissionError) as exc:
                st.error(str(exc))
    with denial_col:
        if st.button("Deny request", key=f"bridge_deny_{request_id}"):
            try:
                auth_store.deny_access_request(request_id, reviewer_user.id)
                st.success("Access request denied.")
                st.rerun()
            except (InvalidAccessRequestError, PermissionError) as exc:
                st.error(str(exc))


def render_sponsor_request_history(auth_store, reviewer_user) -> None:
    if not reviewer_user.is_sponsor and not reviewer_user.is_admin:
        return

    reviewable_requests = auth_store.list_reviewable_requests(reviewer_user)
    heading = "Approval requests" if reviewer_user.is_admin else "Sponsor requests"
    with st.expander(heading, expanded=False):
        if not reviewable_requests:
            st.write("No access requests yet.")
            return
        for request in reviewable_requests:
            review_link = f"?approve_request={request['id']}"
            st.write(
                f"- {request['status']}: {request['suggested_user_category']} "
                f"({request['affiliation']}) [Open request]({review_link})"
            )
