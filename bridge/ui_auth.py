from __future__ import annotations

import datetime

import streamlit as st

from bridge.auth_store import InvalidLoginCodeError, normalize_email
from bridge.bootstrap import write_authenticated_user
from bridge.emailer import send_login_code_email
from bridge.session_cookie import set_session_cookie


def render_deployment_banner(settings) -> None:
    if settings.deployment_label:
        st.caption(settings.deployment_label)
    if settings.deployment_notice:
        st.warning(settings.deployment_notice)


def render_bridge_login(settings, auth_store, session_state) -> None:
    render_deployment_banner(settings)
    st.title("Login")
    email_input = st.text_input("KU Email", value=session_state.get("bridge_pending_email", ""), key="bridge_login_email")

    if st.button("Send one-time code", key="bridge_send_code"):
        try:
            normalized_email = normalize_email(email_input)
            login_code = auth_store.issue_login_code(normalized_email)
            send_login_code_email(settings, normalized_email, login_code)
            session_state["bridge_pending_email"] = normalized_email
            st.success(f"A login code was sent to {normalized_email}.")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Unable to send login code: {exc}")

    pending_email = session_state.get("bridge_pending_email", "")
    if pending_email:
        login_code = st.text_input("One-time code", key="bridge_login_code")
        if st.button("Verify code", key="bridge_verify_code"):
            try:
                user = auth_store.verify_login_code(pending_email, login_code)
                raw_session_token = auth_store.create_session(user.id)
                cookie_expiry = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=settings.session_ttl_hours)
                set_session_cookie(settings.session_cookie_name, raw_session_token, cookie_expiry)
                write_authenticated_user(session_state, user)
                session_state["bridge_pending_email"] = ""
                st.rerun()
            except InvalidLoginCodeError as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Unable to complete sign-in: {exc}")
