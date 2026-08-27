"""User-facing Model Refinement and Human Model Quality Review workflow."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import os
from pathlib import Path

from modules.model_quality.contract import (
    build_refinement_request,
    load_quality_profile,
)
from modules.model_quality.repository import ModelQualityRepository
from modules.model_quality.service import ModelQualityLiveService
from modules.target_model_formulation.live_review import (
    TargetModelFormulationLiveReviewService,
)
from modules.target_model_formulation.repository import (
    TargetModelFormulationAuthorityRepository,
)


_DEFAULT_REFINEMENT_MODEL = "gpt-5.5"


def render_model_refinement_review(
    st,
    *,
    project_id: str,
    base_model,
    write_service,
    technical: bool = False,
) -> None:
    """Render the authority-preserving refinement path for one exact base IEM."""

    repo_root = Path(write_service.project_root)
    projects_root = repo_root / "data" / "projects"

    st.markdown("**Model Refinement**")
    st.caption(
        "Refine model-facing wording without changing approved engineering meaning, "
        "placement or relationship authority. Human review is required before "
        "SysML v2 generation."
    )
    st.caption(
        f"Base model: {base_model.internal_engineering_model_id} · "
        f"{len(base_model.elements)} elements · "
        f"{len(base_model.relationships)} relationships"
    )

    reviewer = st.text_input(
        "Reviewer",
        key=f"model_refinement.reviewer.{project_id}.{base_model.internal_engineering_model_id}",
        placeholder="Reviewer identity",
    ).strip()

    formulation_authority = _render_model_formulation(
        st,
        project_id=project_id,
        base_model=base_model,
        repo_root=repo_root,
        projects_root=projects_root,
        reviewer=reviewer,
        technical=technical,
    )
    if formulation_authority is None:
        st.warning(
            "SysML v2 generation is locked until the required model formulation "
            "decisions are Human-authorized."
        )
        return

    quality_authority = _render_model_quality_review(
        st,
        project_id=project_id,
        base_model=base_model,
        repo_root=repo_root,
        projects_root=projects_root,
        reviewer=reviewer,
        technical=technical,
    )
    if quality_authority is None:
        st.warning(
            "SysML v2 generation is locked until Model Quality Review is complete."
        )
        return

    successor = _render_approved_model(
        st,
        project_id=project_id,
        base_model=base_model,
        formulation_authority=formulation_authority,
        quality_authority=quality_authority,
        write_service=write_service,
        technical=technical,
    )
    if successor is None:
        return

    return successor


def _render_model_formulation(
    st,
    *,
    project_id,
    base_model,
    repo_root,
    projects_root,
    reviewer,
    technical,
):
    st.markdown("**Model formulation**")

    repository = TargetModelFormulationAuthorityRepository(projects_root)
    service = TargetModelFormulationLiveReviewService(
        projects_root=projects_root,
        repo_root=repo_root,
        authority_repository=repository,
    )

    try:
        review = repository.find_review_for_source(
            project_id,
            base_model.internal_engineering_model_id,
            base_model.content_fingerprint,
        )
    except Exception:
        st.error("Model formulation state could not be loaded safely.")
        return None

    if review is None:
        st.info(
            "No model formulation review exists yet for this exact Internal Model."
        )
        if st.button(
            "Prepare model formulation review",
            key=f"model_refinement.formulation.prepare.{base_model.content_fingerprint}",
        ):
            try:
                service.prepare_review(
                    project_id=project_id,
                    internal_engineering_model_id=(
                        base_model.internal_engineering_model_id
                    ),
                )
            except Exception:
                st.error("Model formulation review could not be prepared safely.")
                return None
            _rerun(st)
        return None

    try:
        state = service.state(review)
    except Exception:
        st.error("Model formulation review state could not be reconstructed safely.")
        return None

    decided = {
        item.authority_subject_id: item
        for item in state.effective_decisions
    }
    total = len(review.items)
    st.caption(f"{len(decided)} / {total} formulation decisions reviewed")

    if state.authority_set is not None:
        st.success("Model formulation Human review completed.")
        if technical:
            st.caption(
                f"Review: {review.review_id} · Authority: "
                f"{_authority_id(state.authority_set)}"
            )
        return state.authority_set

    for item in review.items:
        if item.authority_subject_id in decided:
            continue
        with st.container(border=True):
            st.markdown(
                f"**{_humanize(item.current_engineering_type)} · "
                f"{_humanize(item.current_target_representation)}**"
            )
            if technical:
                st.caption(
                    f"{item.authority_subject_id} · {item.subject_kind}"
                )

            options = tuple(item.candidates)
            selected = (
                options[0]
                if len(options) == 1
                else st.selectbox(
                    "Formulation option",
                    options=options,
                    format_func=_formulation_candidate_label,
                    key=(
                        "model_refinement.formulation.candidate."
                        f"{review.review_id}.{item.authority_subject_id}"
                    ),
                )
            )
            _render_formulation_candidate(st, selected, technical=technical)
            rationale = st.text_area(
                "Human rationale",
                key=(
                    "model_refinement.formulation.rationale."
                    f"{review.review_id}.{item.authority_subject_id}"
                ),
                placeholder="Why is this formulation appropriate?",
            ).strip()
            if st.button(
                "Accept formulation",
                key=(
                    "model_refinement.formulation.accept."
                    f"{review.review_id}.{item.authority_subject_id}"
                ),
            ):
                if not reviewer:
                    st.error("Enter the reviewer identity first.")
                    return None
                if not rationale:
                    st.error("Provide a Human rationale for this formulation decision.")
                    return None
                try:
                    service.record_selection(
                        review=review,
                        authority_subject_id=item.authority_subject_id,
                        selected_candidate_id=selected.candidate_id,
                        reviewer_identity=reviewer,
                        rationale=rationale,
                    )
                except Exception:
                    st.error("Model formulation decision could not be recorded safely.")
                    return None
                _rerun(st)
                return None

    if len(decided) == total:
        if st.button(
            "Finalize model formulation",
            key=f"model_refinement.formulation.finalize.{review.review_id}",
        ):
            if not reviewer:
                st.error("Enter the reviewer identity first.")
                return None
            try:
                service.finalize(review)
            except Exception:
                st.error("Model formulation authority could not be finalized safely.")
                return None
            _rerun(st)

    return None


def _render_model_quality_review(
    st,
    *,
    project_id,
    base_model,
    repo_root,
    projects_root,
    reviewer,
    technical,
):
    st.markdown("**Human Model Quality Review**")
    st.caption(
        "Compare the approved model content with the refined model-facing wording. "
        "Accept, modify or reject each refinement proposal."
    )

    try:
        profile = load_quality_profile(
            repo_root / "context/model_quality/model_quality_profile.json"
        )
        request_probe = build_refinement_request(
            snapshot=base_model,
            quality_profile=profile,
        )
        repository = ModelQualityRepository(projects_root)
        existing = repository.find_review_for_source(
            project_id,
            base_model.internal_engineering_model_id,
            base_model.content_fingerprint,
            request_probe.request_fingerprint,
        )
    except Exception:
        st.error("Model refinement state could not be loaded safely.")
        return None

    if existing is None:
        st.info("No refinement proposals exist yet for this exact Internal Model.")
        model = st.text_input(
            "Refinement model",
            value=_DEFAULT_REFINEMENT_MODEL,
            key=(
                "model_refinement.execution.model."
                f"{base_model.internal_engineering_model_id}"
            ),
        ).strip() or _DEFAULT_REFINEMENT_MODEL
        api_key = None
        if not os.getenv("OPENAI_API_KEY"):
            for session_key in (
                "turing_generator.execution_api_key",
                "guided_model.initial.api_key",
                "guided_model.regeneration.api_key",
            ):
                existing_key = st.session_state.get(session_key)
                if isinstance(existing_key, str) and existing_key.strip():
                    api_key = existing_key.strip()
                    break
            if api_key is None:
                api_key = st.text_input(
                    "OpenAI API key for this refinement run",
                    type="password",
                    key=(
                        "model_refinement.execution.api_key."
                        f"{base_model.internal_engineering_model_id}"
                    ),
                    help=(
                        "Used only for this execution. The key is not persisted "
                        "in project evidence."
                    ),
                ).strip() or None
            elif technical:
                st.caption("Using the OpenAI API key already entered in this app session.")

        if st.button(
            "Generate refinement proposals",
            key=f"model_refinement.generate.{base_model.content_fingerprint}",
        ):
            if os.getenv("OPENAI_API_KEY") is None and api_key is None:
                st.error("LLM-assisted refinement requires an OpenAI API key.")
                return None
            try:
                service = ModelQualityLiveService(
                    projects_root=projects_root,
                    repo_root=repo_root,
                    provider="openai",
                    model=model,
                    api_key=api_key,
                )
                spinner = getattr(st, "spinner", None)
                if callable(spinner):
                    with spinner(
                        "Refining model wording while preserving approved semantics..."
                    ):
                        service.prepare(
                            project_id=project_id,
                            internal_engineering_model_id=(
                                base_model.internal_engineering_model_id
                            ),
                        )
                else:
                    service.prepare(
                        project_id=project_id,
                        internal_engineering_model_id=(
                            base_model.internal_engineering_model_id
                        ),
                    )
            except Exception:
                st.error(
                    "Model refinement failed safely. The base Internal Model remains unchanged."
                )
                return None
            _rerun(st)
        return None

    # Existing exact review: prepare() is resumable and returns the persisted bundle
    # without invoking the LLM again.
    service = ModelQualityLiveService(
        projects_root=projects_root,
        repo_root=repo_root,
        repository=repository,
    )
    try:
        request, bundle = service.prepare(
            project_id=project_id,
            internal_engineering_model_id=base_model.internal_engineering_model_id,
        )
        effective = service.effective_decisions(bundle)
        authority = repository.latest_authority_set_for_review(
            project_id,
            bundle.review_id,
        )
    except Exception:
        st.error("Existing Model Quality Review could not be resumed safely.")
        return None

    decisions = {
        item.internal_model_element_id: item
        for item in effective
    }
    st.caption(f"{len(decisions)} / {len(bundle.proposals)} elements reviewed")

    if authority is not None:
        st.success("Model Quality Review completed and Human-authorized.")
        if technical:
            st.caption(
                f"Review: {bundle.review_id} · Authority: "
                f"{_authority_id(authority)}"
            )
        return authority

    input_by_id = {
        item.internal_model_element_id: item
        for item in request.elements
    }
    for proposal in bundle.proposals:
        source = input_by_id[proposal.internal_model_element_id]
        current = decisions.get(proposal.internal_model_element_id)
        _render_quality_card(
            st,
            service=service,
            bundle=bundle,
            source=source,
            proposal=proposal,
            current_decision=current,
            reviewer=reviewer,
            technical=technical,
        )

    effective = service.effective_decisions(bundle)
    all_decided = len(effective) == len(bundle.proposals)
    rejected = tuple(item for item in effective if item.decision == "rejected")

    if rejected:
        st.warning(
            "At least one refinement proposal is rejected. Revise that Human decision "
            "after correcting or overriding the proposal before finalization."
        )
    elif all_decided:
        if st.button(
            "Finalize Model Quality Review",
            key=f"model_refinement.quality.finalize.{bundle.review_id}",
        ):
            if not reviewer:
                st.error("Enter the reviewer identity first.")
                return None
            try:
                service.finalize(bundle)
            except Exception:
                st.error("Model Quality Review could not be finalized safely.")
                return None
            _rerun(st)

    return None


def _render_quality_card(
    st,
    *,
    service,
    bundle,
    source,
    proposal,
    current_decision,
    reviewer,
    technical,
) -> None:
    element_id = proposal.internal_model_element_id
    with st.container(border=True):
        st.markdown(f"**{proposal.refined_name}**")
        st.caption(
            f"{_humanize(source.element_type)} · {_humanize(source.model_area)}"
        )
        if technical:
            st.caption(f"{element_id} · Framework: {source.framework_assignment}")

        columns = st.columns(2)
        with columns[0]:
            st.markdown("**Current**")
            st.write(source.original_name)
            if source.original_description:
                st.write(source.original_description)
        with columns[1]:
            st.markdown("**Proposed**")
            st.write(proposal.refined_name)
            if proposal.refined_description:
                st.write(proposal.refined_description)

        if proposal.quality_findings:
            st.markdown("**Findings**")
            for finding in proposal.quality_findings:
                st.write(f"• {finding}")
        if proposal.requires_human_attention:
            st.warning("This refinement explicitly requires Human attention.")
        if not proposal.meaning_preserved or proposal.unsupported_information_added:
            st.error(
                "This proposal cannot be accepted unchanged because its quality flags "
                "do not confirm meaning preservation."
            )
        if technical:
            st.caption(
                "Quality flags: "
                f"meaning_preserved={proposal.meaning_preserved} · "
                "unsupported_information_added="
                f"{proposal.unsupported_information_added} · "
                f"human_attention={proposal.requires_human_attention}"
            )
            st.caption(f"Agent rationale: {proposal.rationale}")

        if current_decision is not None:
            label = {
                "approved": "Accepted",
                "overridden": "Modified",
                "rejected": "Rejected proposal",
            }.get(current_decision.decision, current_decision.decision)
            if current_decision.decision == "rejected":
                st.warning(f"Current Human decision: {label}")
            else:
                st.success(f"Current Human decision: {label}")
            if current_decision.rationale:
                st.caption(current_decision.rationale)
            if technical:
                st.caption(f"Decision: {current_decision.decision_id}")
            with st.expander("Revise decision"):
                _render_quality_actions(
                    st,
                    service=service,
                    bundle=bundle,
                    source=source,
                    proposal=proposal,
                    reviewer=reviewer,
                    key_suffix=f"revise.{current_decision.decision_id}",
                )
            return

        _render_quality_actions(
            st,
            service=service,
            bundle=bundle,
            source=source,
            proposal=proposal,
            reviewer=reviewer,
            key_suffix="initial",
        )


def _render_quality_actions(
    st,
    *,
    service,
    bundle,
    source,
    proposal,
    reviewer,
    key_suffix,
):
    element_id = proposal.internal_model_element_id
    key_base = f"model_refinement.quality.{bundle.review_id}.{element_id}.{key_suffix}"
    safe_accept = (
        proposal.meaning_preserved
        and not proposal.unsupported_information_added
    )

    columns = st.columns(3)
    if columns[0].button(
        "Accept",
        key=f"{key_base}.accept",
        disabled=not safe_accept,
    ):
        if not reviewer:
            st.error("Enter the reviewer identity first.")
            return
        try:
            service.decide(
                bundle=bundle,
                internal_model_element_id=element_id,
                decision="approved",
                reviewer_identity=reviewer,
                rationale=(
                    "Human reviewed the refined model-facing wording and accepted it unchanged."
                ),
            )
        except Exception:
            st.error("The refinement decision could not be recorded safely.")
            return
        _rerun(st)
        return

    modify_open = columns[1].button(
        "Modify",
        key=f"{key_base}.modify_open",
    )
    reject_open = columns[2].button(
        "Reject proposal",
        key=f"{key_base}.reject_open",
    )

    modify_flag = f"{key_base}.modify_visible"
    reject_flag = f"{key_base}.reject_visible"
    if modify_open:
        st.session_state[modify_flag] = True
        st.session_state[reject_flag] = False
    if reject_open:
        st.session_state[reject_flag] = True
        st.session_state[modify_flag] = False

    if st.session_state.get(modify_flag, False):
        st.markdown("**Modify proposed wording**")
        name = st.text_input(
            "Approved name",
            value=proposal.refined_name,
            key=f"{key_base}.modified_name",
        ).strip()
        description = st.text_area(
            "Approved description",
            value=proposal.refined_description or "",
            key=f"{key_base}.modified_description",
        ).strip()
        rationale = st.text_area(
            "Modification rationale",
            key=f"{key_base}.modified_rationale",
            placeholder="Why is the Human modification required?",
        ).strip()
        if st.button("Save modification", key=f"{key_base}.save_modified"):
            if not reviewer:
                st.error("Enter the reviewer identity first.")
                return
            if not name or not rationale:
                st.error("Approved name and Human rationale are required.")
                return
            try:
                service.decide(
                    bundle=bundle,
                    internal_model_element_id=element_id,
                    decision="overridden",
                    reviewer_identity=reviewer,
                    rationale=rationale,
                    approved_name=name,
                    approved_description=description or None,
                )
            except Exception:
                st.error("The modified refinement decision could not be recorded safely.")
                return
            _rerun(st)
            return

    if st.session_state.get(reject_flag, False):
        st.markdown("**Reject this refinement proposal**")
        st.caption(
            "This rejects only the proposed wording. It does not remove the model element."
        )
        rationale = st.text_area(
            "Rejection rationale",
            key=f"{key_base}.rejection_rationale",
            placeholder="Why is this refinement proposal not acceptable?",
        ).strip()
        if st.button("Confirm rejection", key=f"{key_base}.confirm_reject"):
            if not reviewer:
                st.error("Enter the reviewer identity first.")
                return
            if not rationale:
                st.error("Provide a Human rationale for the rejection.")
                return
            try:
                service.decide(
                    bundle=bundle,
                    internal_model_element_id=element_id,
                    decision="rejected",
                    reviewer_identity=reviewer,
                    rationale=rationale,
                )
            except Exception:
                st.error("The rejection decision could not be recorded safely.")
                return
            _rerun(st)


def _render_approved_model(
    st,
    *,
    project_id,
    base_model,
    formulation_authority,
    quality_authority,
    write_service,
    technical,
):
    st.markdown("**Approved Model**")

    tfa_id = _authority_id(formulation_authority)
    mqa_id = _authority_id(quality_authority)
    try:
        successors = write_service.list_refined_internal_models(
            project_id,
            base_model.internal_engineering_model_id,
        )
    except Exception:
        st.error("Approved-model state could not be loaded safely.")
        return None

    exact = tuple(
        item for item in successors
        if item.get("target_model_formulation_authority_set_id") == tfa_id
        and item.get("model_quality_authority_set_id") == mqa_id
    )
    if len(exact) > 1:
        st.error("Multiple approved models bind the same exact Human authority.")
        return None

    if not exact:
        st.caption(
            "Model formulation and Model Quality Review are complete. Create the "
            "immutable successor Internal Model before generation."
        )
        if st.button(
            "Create approved model",
            key=(
                "model_refinement.successor.create."
                f"{base_model.content_fingerprint}.{tfa_id}.{mqa_id}"
            ),
        ):
            try:
                write_service.materialize_refined_internal_model(
                    project_id,
                    source_snapshot=base_model,
                    target_model_formulation_authority=formulation_authority,
                    model_quality_authority=quality_authority,
                )
            except Exception:
                st.error("Approved model could not be materialized safely.")
                return None
            _rerun(st)
        return None

    model = exact[0]["model"]
    st.success(f"Approved Internal Model: {model.internal_engineering_model_id}")
    st.caption(
        f"{len(model.elements)} elements · {len(model.relationships)} relationships"
    )
    if technical:
        st.caption(
            f"Model formulation authority: {tfa_id} · "
            f"Model quality authority: {mqa_id}"
        )
        st.caption(f"Approved-model fingerprint: {model.content_fingerprint}")
    return model


def _render_generation(
    st,
    *,
    project_id,
    approved_model,
    write_service,
    technical,
):
    st.markdown("**SysML v2 generation**")
    try:
        artifact = write_service.load_authority_backed_sysml(
            project_id,
            approved_model.internal_engineering_model_id,
        )
    except Exception:
        st.error("Generated SysML v2 state could not be loaded safely.")
        return

    if artifact is None:
        if st.button(
            "Generate SysML v2",
            key=(
                "model_refinement.generate_sysml."
                f"{approved_model.content_fingerprint}"
            ),
        ):
            try:
                write_service.generate_authority_backed_sysml(
                    project_id,
                    snapshot=approved_model,
                )
            except Exception:
                st.error(
                    "SysML v2 generation failed safely. The approved model remains unchanged."
                )
                return
            _rerun(st)
        return

    st.success(
        "SysML v2 generated from the Human-authorized approved model. "
        "Continue with Final Model Review."
    )
    if technical:
        fingerprint = getattr(artifact, "content_fingerprint", None)
        if fingerprint:
            st.caption(f"Generated artifact fingerprint: {fingerprint}")


def _render_formulation_candidate(st, candidate, *, technical: bool) -> None:
    st.write(f"Outcome: {_humanize(candidate.relevance_outcome)}")
    if candidate.formulation_text:
        st.code(candidate.formulation_text, language="text")
    if candidate.rationale:
        st.caption(candidate.rationale)
    if candidate.unresolved_questions:
        for question in candidate.unresolved_questions:
            st.warning(question)
    if technical:
        st.caption(
            f"Candidate: {candidate.candidate_id} · "
            f"Pattern: {candidate.target_model_pattern_id or '—'} · "
            f"Notation: {candidate.target_notation_construct_id or '—'}"
        )


def _formulation_candidate_label(candidate) -> str:
    notation = candidate.target_notation_construct_id or "no formal notation"
    return f"{_humanize(candidate.relevance_outcome)} · {notation}"


def _authority_id(value) -> str:
    if isinstance(value, dict):
        return str(value.get("authority_set_id") or "")
    return str(getattr(value, "authority_set_id", ""))


def _authority_payload(value) -> dict:
    if isinstance(value, dict):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError("Authority value must be a dataclass or dict.")


def _humanize(value: str) -> str:
    return str(value).replace("_", " ").replace(".", " · ").strip().title()


def _rerun(st) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()
