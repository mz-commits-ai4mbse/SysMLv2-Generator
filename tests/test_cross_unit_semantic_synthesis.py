from modules.semantic_consolidation.cross_unit_synthesis import (
    LocalElementSubject,
    LocalRelationshipSubject,
    cross_unit_semantic_synthesis_artifact_to_dict,
    synthesize_cross_unit_semantics,
)


def elem(ref, sau, local_id, name, typ='actor'):
    return LocalElementSubject(
        local_subject_ref=ref,
        source_analysis_unit_id=sau,
        local_semantic_subject_id=local_id,
        member_proposal_refs=(f'{ref}/p1',),
        candidate_names=(name,),
        proposed_element_types=(typ,),
        concise_descriptions=(name,),
        evidence_refs=(f'{ref}/e1',),
    )


def rel(ref, sau, local_id, source, target, typ='controls', unresolved_target=None):
    return LocalRelationshipSubject(
        local_subject_ref=ref,
        source_analysis_unit_id=sau,
        local_semantic_subject_id=local_id,
        member_proposal_refs=(f'{ref}/p1',),
        source_local_element_subject_ref=source,
        source_unresolved_endpoint_ref=None,
        target_local_element_subject_ref=(None if unresolved_target else target),
        target_unresolved_endpoint_ref=unresolved_target,
        proposed_relationship_types=(typ,),
        semantic_statements=(f'{source} {typ} {target}',),
        evidence_refs=(f'{ref}/e1',),
    )


def result(groups, comparisons):
    return {
        'schema_version':'1.0.0',
        'method':'semantic_model',
        'trace_ref':'trace:test',
        'groups':[{'member_refs':list(group)} for group in groups],
        'comparisons':comparisons,
    }


def eq(left, right):
    return {'left_ref':left,'right_ref':right,'outcome':'equivalent','rationale':'same'}


def test_cross_unit_elements_merge_and_relationships_rebind():
    elements=(
        elem('SAU-000001#E1','SAU-000001','SEM-000001','Operator'),
        elem('SAU-000001#E2','SAU-000001','SEM-000002','Remote Expert'),
        elem('SAU-000002#E1','SAU-000002','SEM-000001','Microscope Operator'),
        elem('SAU-000002#E2','SAU-000002','SEM-000002','External Expert'),
    )
    relationships=(
        rel('SAU-000001#R1','SAU-000001','SEM-000010','SAU-000001#E1','SAU-000001#E2'),
        rel('SAU-000002#R1','SAU-000002','SEM-000010','SAU-000002#E1','SAU-000002#E2'),
    )
    def ec(payload):
        return result(
            [
                ('SAU-000001#E1','SAU-000002#E1'),
                ('SAU-000001#E2','SAU-000002#E2'),
            ],
            [
                eq('SAU-000001#E1','SAU-000002#E1'),
                eq('SAU-000001#E2','SAU-000002#E2'),
            ],
        )
    def rc(payload):
        assert payload['local_subjects'][0]['source_synthesized_element_subject_id'] == 'SES-000001'
        assert payload['local_subjects'][0]['target_synthesized_element_subject_id'] == 'SES-000002'
        return result(
            [('SAU-000001#R1','SAU-000002#R1')],
            [eq('SAU-000001#R1','SAU-000002#R1')],
        )
    out=synthesize_cross_unit_semantics(
        project_id='887027', processing_run_id='RUN-000001',
        created_at_utc='2026-08-18T20:30:00Z',
        source_analysis_unit_ids=('SAU-000001','SAU-000002'),
        local_element_subjects=elements,
        local_relationship_subjects=relationships,
        element_comparator=ec, relationship_comparator=rc,
    )
    assert len(out.artifact.synthesized_element_subjects)==2
    assert len(out.artifact.synthesized_relationship_subjects)==1
    r=out.artifact.synthesized_relationship_subjects[0]
    assert r.source_synthesized_element_subject_id=='SES-000001'
    assert r.target_synthesized_element_subject_id=='SES-000002'
    assert r.requires_human_review is False
    assert out.element_degraded_to_singletons is False
    assert out.relationship_degraded_to_singletons is False


def test_invalid_element_partition_degrades_to_singletons():
    elements=(
        elem('SAU-000001#E1','SAU-000001','SEM-000001','Expert'),
        elem('SAU-000002#E1','SAU-000002','SEM-000001','Expert'),
    )
    def bad(_payload):
        return result([('SAU-000001#E1',)], [])
    out=synthesize_cross_unit_semantics(
        project_id='887027', processing_run_id='RUN-000001',
        created_at_utc='2026-08-18T20:30:00Z',
        source_analysis_unit_ids=('SAU-000001','SAU-000002'),
        local_element_subjects=elements, local_relationship_subjects=(),
        element_comparator=bad, relationship_comparator=None,
    )
    assert len(out.artifact.synthesized_element_subjects)==2
    assert out.element_degraded_to_singletons is True
    assert out.element_warning_codes==('cross_unit_element_comparator_invalid',)


def test_relationship_comparator_cannot_merge_different_rebound_endpoints():
    elements=(
        elem('SAU-000001#E1','SAU-000001','SEM-1','A'),
        elem('SAU-000001#E2','SAU-000001','SEM-2','B'),
        elem('SAU-000002#E1','SAU-000002','SEM-1','C'),
        elem('SAU-000002#E2','SAU-000002','SEM-2','D'),
    )
    relationships=(
        rel('SAU-000001#R1','SAU-000001','R1','SAU-000001#E1','SAU-000001#E2'),
        rel('SAU-000002#R1','SAU-000002','R1','SAU-000002#E1','SAU-000002#E2'),
    )
    def rc(_payload):
        return result(
            [('SAU-000001#R1','SAU-000002#R1')],
            [eq('SAU-000001#R1','SAU-000002#R1')],
        )
    out=synthesize_cross_unit_semantics(
        project_id='887027', processing_run_id='RUN-000001',
        created_at_utc='2026-08-18T20:30:00Z',
        source_analysis_unit_ids=('SAU-000001','SAU-000002'),
        local_element_subjects=elements, local_relationship_subjects=relationships,
        element_comparator=None, relationship_comparator=rc,
    )
    assert len(out.artifact.synthesized_relationship_subjects)==2
    assert out.relationship_degraded_to_singletons is True
    assert out.relationship_warning_codes==('cross_unit_relationship_comparator_invalid',)


def test_unresolved_endpoint_stays_reviewable_and_is_not_invented():
    elements=(elem('SAU-000001#E1','SAU-000001','SEM-1','Operator'),)
    relationships=(
        rel('SAU-000001#R1','SAU-000001','R1','SAU-000001#E1','missing',unresolved_target='semantic:unresolved:abc'),
    )
    out=synthesize_cross_unit_semantics(
        project_id='887027', processing_run_id='RUN-000001',
        created_at_utc='2026-08-18T20:30:00Z',
        source_analysis_unit_ids=('SAU-000001',),
        local_element_subjects=elements, local_relationship_subjects=relationships,
        element_comparator=None, relationship_comparator=None,
    )
    r=out.artifact.synthesized_relationship_subjects[0]
    assert r.source_synthesized_element_subject_id=='SES-000001'
    assert r.target_synthesized_element_subject_id is None
    assert r.requires_human_review is True
    assert len(out.artifact.relationship_rebinding_findings)==1
    assert out.relationship_warning_codes==(
        'cross_unit_relationship_endpoint_human_review_required',
    )


def test_artifact_fingerprint_is_self_consistent():
    out=synthesize_cross_unit_semantics(
        project_id='887027', processing_run_id='RUN-000001',
        created_at_utc='2026-08-18T20:30:00Z',
        source_analysis_unit_ids=('SAU-000001',),
        local_element_subjects=(elem('SAU-000001#E1','SAU-000001','SEM-1','A'),),
        local_relationship_subjects=(), element_comparator=None, relationship_comparator=None,
    )
    payload=cross_unit_semantic_synthesis_artifact_to_dict(out.artifact)
    assert payload['artifact_fingerprint']==out.artifact.artifact_fingerprint
