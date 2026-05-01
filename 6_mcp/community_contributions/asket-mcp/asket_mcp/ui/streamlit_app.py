from __future__ import annotations

import tempfile
from pathlib import Path

import streamlit as st

from asket_mcp import __version__
from asket_mcp.store.user_profile import get_user_profile_store
from asket_mcp.ui.handlers import (
    COMMON_TIMEZONES,
    chat_bootstrap,
    note_list_short_md,
    profile_save,
    roadmap_coach_hint,
    roadmap_markdown,
    scratch_note_save,
    semantic_knowledge_stats,
    study_partner_turn,
    ui_about,
    ui_brain_delete,
    ui_brain_find,
    ui_brain_list,
    ui_brain_read,
    ui_brain_search,
    ui_brain_write,
    ui_fetch,
    ui_note_create,
    ui_note_delete,
    ui_note_list,
    ui_note_read,
    ui_now,
    ui_push,
    ui_semantic_ask,
    ui_semantic_ingest,
    ui_semantic_search,
)

_PAGE_TITLE = "Personal Study Brain"


def _save_upload_tmp(uploaded) -> str | None:
    if uploaded is None:
        return None
    d = Path(tempfile.mkdtemp(prefix="asket-ui-"))
    p = d / uploaded.name
    p.write_bytes(uploaded.getvalue())
    return str(p)


def main() -> None:
    st.set_page_config(page_title=_PAGE_TITLE, layout="wide", initial_sidebar_state="expanded")

    if "messages" not in st.session_state:
        st.session_state.messages = chat_bootstrap()

    st.sidebar.markdown("### Your folders")
    st.sidebar.caption("Everything in **Study library** is under Brain; scratch notes use SQLite on disk.")
    if st.sidebar.button("Refresh locations"):
        st.session_state.pop("about_sidebar", None)
    about = st.session_state.get("about_sidebar") or ui_about()
    if "about_sidebar" not in st.session_state:
        st.session_state["about_sidebar"] = about
    st.sidebar.code(about, language=None)
    with st.sidebar.expander("Safety & tips", expanded=False):
        st.markdown(
            "- Brain paths are **relative** to the Brain folder.\n"
            "- Writes/deletes need confirmation in **More tools**.\n"
            "- Use **Alerts** only if Pushover is configured."
        )

    st.title(f"Personal Study Brain · v{__version__}")
    st.markdown(
        "**Streamlit UI** — study partner chat below; roadmap / map / scratch in the right column; "
        "**More tools** at the bottom for full CRUD."
    )

    col_chat, col_ctx = st.columns([1, 1], gap="large")

    with col_chat:
        st.subheader("Study partner")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        up = st.file_uploader(
            "Attach .txt, .md, .csv, .pdf, .docx (optional)",
            type=["txt", "md", "markdown", "csv", "pdf", "docx"],
            key="chat_upload",
        )
        c1, c2 = st.columns([1, 3])
        with c1:
            file_only = st.button("Send file only", help="Uses attached file without chat text")
        prompt = st.chat_input("Message, URL, or instructions…")

        path = _save_upload_tmp(up)
        if prompt:
            _, st.session_state.messages = study_partner_turn(
                prompt,
                st.session_state.messages,
                path,
            )
            st.rerun()
        if file_only and path:
            _, st.session_state.messages = study_partner_turn(
                "",
                st.session_state.messages,
                path,
            )
            st.rerun()

    with col_ctx:
        tab_rm, tab_km, tab_sc = st.tabs(["Learning roadmap", "Knowledge map", "Scratch notes"])
        with tab_rm:
            if st.button("Refresh roadmap", key="rd_r"):
                st.session_state.pop("roadmap_md", None)
            if st.button("Coach check-in (LLM)", key="rd_c"):
                st.session_state["roadmap_md"] = roadmap_coach_hint()
            rm = st.session_state.get("roadmap_md") or roadmap_markdown()
            st.markdown(rm)
            st.markdown("##### Profile")
            prof = get_user_profile_store().get_profile()
            g = st.text_area("Goals", value=prof.goals, height=80, key="pf_g")
            lv = st.text_input("Expertise / level", value=prof.expertise_level, key="pf_lv")
            rd = st.text_area("Roadmap (Markdown)", value=prof.roadmap_markdown, height=140, key="pf_rd")
            if st.button("Save profile", key="pf_save"):
                st.session_state["roadmap_md"] = profile_save(g, lv, rd)
                st.rerun()

        with tab_km:
            if st.button("Refresh stats", key="kn_r"):
                st.session_state.pop("kn_stats", None)
            ks = st.session_state.get("kn_stats") or semantic_knowledge_stats()
            st.session_state["kn_stats"] = ks
            st.markdown(ks)
            st.markdown(
                """
<div style="min-height:240px;display:flex;align-items:center;justify-content:center;
background:linear-gradient(145deg,#0b1020,#182848);color:#e8eeff;border-radius:14px;
border:1px solid rgba(129,140,248,.35);padding:1.5rem;text-align:center;">
<strong>Semantic knowledge graph · preview</strong><br/>
<span style="opacity:.9;font-size:.9rem">Chunks in Chroma — live graph (e.g. vis.js) can plug in here.</span>
</div>
""",
                unsafe_allow_html=True,
            )

        with tab_sc:
            st.caption("Quick SQLite note — full list/delete in **More tools**.")
            t = st.text_input("Title", key="sc_t")
            b = st.text_area("Body", height=120, key="sc_b")
            if st.button("Save to SQLite", key="sc_sv"):
                status, lst = scratch_note_save(t, b)
                st.session_state["sc_stat"] = status
                st.session_state["sc_list"] = lst
            if "sc_stat" in st.session_state:
                st.info(st.session_state["sc_stat"])
            st.markdown(st.session_state.get("sc_list") or note_list_short_md())

    with st.expander("More tools — notes, fetch, Brain, semantic batch, alerts, help", expanded=False):
        mt1, mt2, mt3, mt4, mt5, mt6 = st.tabs(
            ["Quick notes", "Read a web page", "Study library", "Semantic memory", "Alerts & clock", "Help"]
        )
        with mt1:
            st.markdown("**Scratch notes** — create, list, read, delete.")
            c11, c12 = st.columns(2)
            with c11:
                nt = st.text_input("Title", key="n_title")
                nb = st.text_area("Details", key="n_body")
                if st.button("Save this note", key="n_create"):
                    st.session_state["n_out"] = ui_note_create(nt, nb)
            with c12:
                if st.button("Refresh list", key="n_list"):
                    st.session_state["n_list_o"] = ui_note_list()
            if "n_out" in st.session_state:
                st.write(st.session_state["n_out"])
            if st.button("Show list now", key="n_list2"):
                st.session_state["n_list_o"] = ui_note_list()
            if "n_list_o" in st.session_state:
                st.text(st.session_state["n_list_o"])
            nr = st.text_input("Note # to open", key="n_read")
            if st.button("Show full note", key="n_read_btn"):
                st.session_state["n_read_o"] = ui_note_read(nr)
            nd = st.text_input("Note # to delete", key="n_del")
            nd_ok = st.checkbox("Yes, delete", key="n_del_ok")
            if st.button("Delete note", key="n_del_btn"):
                st.session_state["n_del_o"] = ui_note_delete(nd, nd_ok)
            if "n_read_o" in st.session_state:
                st.text(st.session_state["n_read_o"])
            if "n_del_o" in st.session_state:
                st.write(st.session_state["n_del_o"])

        with mt2:
            u = st.text_input("URL", placeholder="https://…", key="fetch_u")
            if st.button("Get readable text", key="fetch_go"):
                st.session_state["fetch_o"] = ui_fetch(u)
            if "fetch_o" in st.session_state:
                st.text_area("Page text", st.session_state["fetch_o"], height=400)

        with mt3:
            ld = st.text_input("Folder in Brain", value=".", key="br_ld")
            if st.button("List files", key="br_ld_go"):
                st.session_state["br_ld_o"] = ui_brain_list(ld)
            rp = st.text_input("File to open", key="br_rp")
            if st.button("Open file", key="br_rd_go"):
                st.session_state["br_rp_o"] = ui_brain_read(rp)
            wp = st.text_input("Save path", key="br_wp")
            wb = st.text_area("Content", key="br_wb")
            wo = st.checkbox("Overwrite", key="br_wo")
            if st.button("Save to disk", key="br_w_go"):
                st.session_state["br_w_o"] = ui_brain_write(wp, wb, wo)
            fu, fg = st.columns(2)
            with fu:
                f_u = st.text_input("Find under", value=".", key="br_fu")
                f_g = st.text_input("Glob", value="*.md", key="br_fg")
                if st.button("Find files", key="br_ff"):
                    st.session_state["br_ff_o"] = ui_brain_find(f_u, f_g)
            sq = st.text_input("Search phrase", key="br_sq")
            ss = st.text_input("Under", value=".", key="br_ss")
            if st.button("Search in notes", key="br_ss_go"):
                st.session_state["br_ss_o"] = ui_brain_search(sq, ss)
            dp = st.text_input("Delete path", key="br_dp")
            dok = st.checkbox("Confirm delete file", key="br_dok")
            if st.button("Delete file", key="br_del_go"):
                st.session_state["br_del_o"] = ui_brain_delete(dp, dok)
            if "br_ld_o" in st.session_state:
                st.text_area("List output", st.session_state["br_ld_o"], height=180, key="out_ld")
            if "br_rp_o" in st.session_state:
                st.text_area("Read output", st.session_state["br_rp_o"], height=220, key="out_rp")
            if "br_w_o" in st.session_state:
                st.text("Write: " + st.session_state["br_w_o"])
            if "br_ff_o" in st.session_state:
                st.text_area("Find files", st.session_state["br_ff_o"], height=160, key="out_ff")
            if "br_ss_o" in st.session_state:
                st.text_area("Search matches", st.session_state["br_ss_o"], height=200, key="out_ss")
            if "br_del_o" in st.session_state:
                st.text("Delete: " + st.session_state["br_del_o"])

        with mt4:
            sb = st.text_area("Text to ingest", key="sem_b")
            sl = st.text_input("Label / source_id", key="sem_l")
            if st.button("Ingest text", key="sem_ing"):
                st.session_state["sem_ing_o"] = ui_semantic_ingest(sb, sl)
            sq2 = st.text_input("Search by meaning", key="sem_q")
            if st.button("Search memory", key="sem_sq"):
                st.session_state["sem_sq_o"] = ui_semantic_search(sq2)
            sa = st.text_input("Ask the brain (RAG)", key="sem_a")
            if st.button("Get answer", key="sem_a_go"):
                st.session_state["sem_a_o"] = ui_semantic_ask(sa)
            for k, h in (
                ("sem_ing_o", 80),
                ("sem_sq_o", 200),
                ("sem_a_o", 200),
            ):
                if k in st.session_state:
                    st.text_area(k, st.session_state[k], height=h)

        with mt5:
            pm = st.text_area("Pushover message", key="push_m")
            if st.button("Send alert", key="push_go"):
                st.session_state["push_o"] = ui_push(pm)
            tz = st.selectbox("Timezone", COMMON_TIMEZONES, index=0)
            tz_c = st.text_input("Or custom tz", value="", key="tz_c")
            use = tz_c.strip() or tz
            if st.button("Show time", key="tz_go"):
                st.session_state["tz_o"] = ui_now(use)
            if "push_o" in st.session_state:
                st.write(st.session_state["push_o"])
            if "tz_o" in st.session_state:
                st.code(st.session_state["tz_o"])

        with mt6:
            st.markdown("### Help")
            st.markdown(
                "This browser app mirrors **asket-mcp** libraries. For IDE use, run **`uv run asket-mcp`** (stdio)."
            )
            if st.button("Refresh technical summary", key="ab_go"):
                st.session_state["ab_o"] = ui_about()
            if "ab_o" in st.session_state:
                st.code(st.session_state["ab_o"])


if __name__ == "__main__":
    main()
