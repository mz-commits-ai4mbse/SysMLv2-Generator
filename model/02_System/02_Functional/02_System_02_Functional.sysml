package Turing_System_Functional {

    doc /*
    Purpose:
    This package documents the system functions of the Turing Generator.

    Modeling status:
    Transitional SysIDE shadow model.

    Scope:
    The functions describe what the system does on system functional level.
    They do not yet define Python modules, classes, scripts or deployment structures.

    Relation to requirements:
    System functions are derived from system requirements and design constraints.
    Detailed traceability is documented in doc blocks to avoid broken references to other shadow model files.

    Completeness:
    This version covers all 39 system requirements and all 15 system design constraints at least once.
    */

    package '00_FunctionDefinitions' {

        action def ExecuteTuringTransformationWorkflow {
            doc /*
            Main end to end system function.

            The function coordinates the transformation of machine readable legacy engineering data into
            generated SysML v2 artifacts through ingestion, extraction, normalization, candidate generation,
            human review and artifact generation.

            This is the functional representation of the overall Turing Generator workflow.
            */
        }

        action def IngestLegacyData {
            doc /*
            The system receives machine readable legacy engineering data artifacts from the user or an external source.

            Derived from:
            SYSR_001 IngestMachineReadableLegacyData
            SYSR_035 SupportFileUploadInUserInterface
            */
        }

        action def ExtractInformation {
            doc /*
            The system extracts text, tables or structured content from ingested legacy engineering artifacts.

            Derived from:
            SYSR_002 ExtractInformationFromLegacyArtifacts
            */
        }

        action def NormalizeToCanonicalRepresentation {
            doc /*
            The system normalizes extracted information into an internal canonical representation.

            The intended internal representation is JSON, but this function remains on system functional level.

            Derived from:
            SYSR_003 NormalizeToCanonicalJson
            SYSC_013 CanonicalJsonIntermediateRepresentation
            */
        }

        action def CreateNormalizedInformationUnits {
            doc /*
            The system divides normalized information into bounded and source traceable normalized information units.

            Derived from:
            SYSR_004 PreserveSourceMetadata
            SYSR_005 SplitInformationIntoNormalizedInformationUnits
            */
        }

        action def AssessInformationQuality {
            doc /*
            The system assesses normalized information units for completeness, consistency, machine readability,
            reliability and relevance.

            Derived from:
            SYSR_006 AssessNormalizedInformationUnitQuality
            */
        }

        action def SupportControlledDataCompletion {
            doc /*
            The system supports controlled completion of incomplete legacy data using human supplied information.

            This function is part of the target architecture and may be limited in the MVP.

            Derived from:
            SYSR_007 SupportControlledDataCompletion
            */
        }

        action def GenerateCandidateResults {
            doc /*
            The system generates candidate results for selected processing tasks.

            The architecture may realize this through multiple configurable agent profiles, but this function
            describes the system capability rather than the concrete implementation.

            Derived from:
            SYSR_008 GenerateCandidateResults
            SYSR_009 SupportConfigurableCandidateGeneration
            SYSC_005 MultipleConfigurableAgentProfiles
            SYSC_006 ScalableAgentProfileCount
            */
        }

        action def CompareCandidateResults {
            doc /*
            The system compares candidate results generated for the same processing task.

            Derived from:
            SYSR_011 CompareCandidateResults
            SYSR_012 PresentCandidateDifferences
            SYSR_013 PresentCandidateAgreement
            */
        }

        action def GenerateReviewReport {
            doc /*
            The system generates review reports that present candidate results, identified differences,
            rationales, source references and required human decisions.

            Derived from:
            SYSR_010 GenerateCandidateRationales
            SYSR_014 GenerateReviewReport
            SYSR_018 ExplainModelingDecisions
            */
        }

        action def CaptureHumanDecision {
            doc /*
            The system captures the human review decision and records whether an intermediate result is accepted,
            rejected or modified.

            Derived from:
            SYSR_015 RequireHumanApproval
            SYSR_016 ProvideHumanDecisionOptions
            SYSR_017 RecordHumanDecision
            SYSC_007 HumanApprovalIndependentOfCandidateAgreement
            */
        }

        action def AlignTerminology {
            doc /*
            The system aligns extracted terms with a defined technical vocabulary before model synthesis.

            This function is part of the target architecture and may be limited in the MVP.

            Derived from:
            SYSR_019 AlignTermsWithVocabulary
            */
        }

        action def DetectSemanticConflicts {
            doc /*
            The system identifies ontology or vocabulary conflicts in candidate results.

            This function is part of the target architecture and may be limited in the MVP.

            Derived from:
            SYSR_020 DetectSemanticConflicts
            */
        }

        action def ApplyArchitectureConstraints {
            doc /*
            The system applies defined architectural constraints during model synthesis.

            This function is part of the target architecture and may be limited in the MVP.

            Derived from:
            SYSR_021 ApplyArchitectureConstraints
            */
        }

        action def GenerateSysMLv2Artifacts {
            doc /*
            The system generates SysML v2 textual artifacts according to a defined target notation and target project structure.

            Derived from:
            SYSR_022 GenerateModularTargetModelStructures
            SYSR_024 GenerateSysMLv2TargetNotation
            SYSR_025 GenerateTargetProjectStructure
            SYSR_026 PreserveTraceabilityInGeneratedModel
            SYSC_008 DefinedSysMLv2TargetNotation
            SYSC_009 DefinedTargetProjectStructure
            */
        }

        action def MaintainInteractionAndInterfaceConsistency {
            doc /*
            The system maintains consistency of generated interaction and interface related model elements.

            This function is part of the post MVP target architecture.

            Derived from:
            SYSR_023 MaintainGeneratedInteractionAndInterfaceConsistency
            */
        }

        action def PrepareValidationWorkflow {
            doc /*
            The system prepares generated SysML v2 artifacts for validation by the selected validation environment.

            Derived from:
            SYSR_027 SupportValidationWorkflow
            SYSR_028 ReportValidationFindings
            SYSC_010 ToolchainValidationCompatibility
            */
        }

        action def ProvideUserInteraction {
            doc /*
            The system provides user interaction capabilities for upload, preview, review, decision capture and access
            to generated SysML v2 artifacts.

            This function is a supporting cross cutting system function and is not limited to one single workflow step.

            Derived from:
            SYSR_034 ProvideRudimentaryUserInterface
            SYSR_035 SupportFileUploadInUserInterface
            SYSR_036 PresentIngestionPreview
            SYSR_037 PresentReviewReportsInUserInterface
            SYSR_038 CaptureHumanReviewDecision
            SYSR_039 ProvideAccessToGeneratedSysMLv2Artifacts
            SYSC_014 UserInterfaceThroughOrchestrationInterface
            SYSC_015 RudimentaryMVPUserInterface
            */
        }

        action def SupportExtensiblePipelineExecution {
            doc /*
            The system supports extensible and configurable execution of selected pipeline capabilities.

            This function prepares the later allocation to an orchestration component.

            Derived from:
            SYSR_029 ProvideExtensibleProcessingStructure
            SYSR_030 SeparateControlFlowFromProcessingCapabilities
            SYSR_031 AssignDistinctProcessingResponsibilities
            SYSR_032 SupportExtensionThroughDefinedModuleInterfaces
            SYSR_033 SupportConfigurablePipelineExecution
            SYSC_001 ModularPipelineArchitecture
            SYSC_002 CentralOrchestration
            SYSC_003 DefinedModuleInterfaces
            SYSC_004 MVPAsTargetArchitectureSubset
            SYSC_011 PythonModuleBasedImplementation
            SYSC_012 OrchestratorControlledExecution
            */
        }
    }

    package '01_EndToEndWorkflow' {

        action executeTuringTransformationWorkflow : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            End to end workflow description:

            1. Ingest legacy data.
            2. Extract information.
            3. Normalize information to a canonical representation.
            4. Create normalized information units.
            5. Assess information quality.
            6. Support controlled data completion if required.
            7. Generate candidate results.
            8. Compare candidate results.
            9. Generate review report.
            10. Capture human decision.
            11. Align terminology if required by the selected pipeline configuration.
            12. Detect semantic conflicts if required by the selected pipeline configuration.
            13. Apply architecture constraints if required by the selected pipeline configuration.
            14. Generate SysML v2 artifacts.
            15. Maintain interaction and interface consistency if required by the selected pipeline configuration.
            16. Prepare validation workflow.
            17. Provide user interaction throughout relevant workflow steps.
            18. Support extensible pipeline execution as cross cutting workflow capability.

            Note:
            The detailed control flow is intentionally documented as text in this transitional SysIDE model.
            A later CATIA model can represent the same sequence graphically as an activity or action flow.
            */

            action ingestLegacyData : '00_FunctionDefinitions'::IngestLegacyData;
            action extractInformation : '00_FunctionDefinitions'::ExtractInformation;
            action normalizeToCanonicalRepresentation : '00_FunctionDefinitions'::NormalizeToCanonicalRepresentation;
            action createNormalizedInformationUnits : '00_FunctionDefinitions'::CreateNormalizedInformationUnits;
            action assessInformationQuality : '00_FunctionDefinitions'::AssessInformationQuality;
            action supportControlledDataCompletion : '00_FunctionDefinitions'::SupportControlledDataCompletion;
            action generateCandidateResults : '00_FunctionDefinitions'::GenerateCandidateResults;
            action compareCandidateResults : '00_FunctionDefinitions'::CompareCandidateResults;
            action generateReviewReport : '00_FunctionDefinitions'::GenerateReviewReport;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action alignTerminology : '00_FunctionDefinitions'::AlignTerminology;
            action detectSemanticConflicts : '00_FunctionDefinitions'::DetectSemanticConflicts;
            action applyArchitectureConstraints : '00_FunctionDefinitions'::ApplyArchitectureConstraints;
            action generateSysMLv2Artifacts : '00_FunctionDefinitions'::GenerateSysMLv2Artifacts;
            action maintainInteractionAndInterfaceConsistency : '00_FunctionDefinitions'::MaintainInteractionAndInterfaceConsistency;
            action prepareValidationWorkflow : '00_FunctionDefinitions'::PrepareValidationWorkflow;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
            action supportExtensiblePipelineExecution : '00_FunctionDefinitions'::SupportExtensiblePipelineExecution;
        }
    }

    package '02_FunctionDecomposition' {

        action dataPreparation : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Data preparation groups the functions required to transform heterogeneous legacy artifacts into
            normalized and source traceable information units.

            Included functions:
            IngestLegacyData
            ExtractInformation
            NormalizeToCanonicalRepresentation
            CreateNormalizedInformationUnits
            SupportControlledDataCompletion
            */

            action ingestLegacyData : '00_FunctionDefinitions'::IngestLegacyData;
            action extractInformation : '00_FunctionDefinitions'::ExtractInformation;
            action normalizeToCanonicalRepresentation : '00_FunctionDefinitions'::NormalizeToCanonicalRepresentation;
            action createNormalizedInformationUnits : '00_FunctionDefinitions'::CreateNormalizedInformationUnits;
            action supportControlledDataCompletion : '00_FunctionDefinitions'::SupportControlledDataCompletion;
        }

        action candidateGenerationAndAssessment : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Candidate generation and assessment groups the functions required to assess data quality,
            generate candidate results and compare them for human review.

            Included functions:
            AssessInformationQuality
            GenerateCandidateResults
            CompareCandidateResults
            */

            action assessInformationQuality : '00_FunctionDefinitions'::AssessInformationQuality;
            action generateCandidateResults : '00_FunctionDefinitions'::GenerateCandidateResults;
            action compareCandidateResults : '00_FunctionDefinitions'::CompareCandidateResults;
        }

        action semanticAndArchitectureGuardrails : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Semantic and architecture guardrails group functions that align terminology, detect semantic conflicts
            and apply architectural constraints before or during model synthesis.

            Included functions:
            AlignTerminology
            DetectSemanticConflicts
            ApplyArchitectureConstraints
            MaintainInteractionAndInterfaceConsistency
            */

            action alignTerminology : '00_FunctionDefinitions'::AlignTerminology;
            action detectSemanticConflicts : '00_FunctionDefinitions'::DetectSemanticConflicts;
            action applyArchitectureConstraints : '00_FunctionDefinitions'::ApplyArchitectureConstraints;
            action maintainInteractionAndInterfaceConsistency : '00_FunctionDefinitions'::MaintainInteractionAndInterfaceConsistency;
        }

        action humanReview : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Human review groups the functions required to make candidate results understandable and controllable
            by the engineer or responsible human role.

            Included functions:
            GenerateReviewReport
            CaptureHumanDecision
            ProvideUserInteraction
            */

            action generateReviewReport : '00_FunctionDefinitions'::GenerateReviewReport;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
        }

        action synthesisAndValidation : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Synthesis and validation groups the functions required to generate SysML v2 artifacts and prepare
            them for validation.

            Included functions:
            GenerateSysMLv2Artifacts
            PrepareValidationWorkflow
            */

            action generateSysMLv2Artifacts : '00_FunctionDefinitions'::GenerateSysMLv2Artifacts;
            action prepareValidationWorkflow : '00_FunctionDefinitions'::PrepareValidationWorkflow;
        }

        action extensiblePipelineSupport : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Extensible pipeline support groups the cross cutting capability that enables the MVP to be implemented
            as a selected subset of the later target architecture.

            Included function:
            SupportExtensiblePipelineExecution
            */

            action supportExtensiblePipelineExecution : '00_FunctionDefinitions'::SupportExtensiblePipelineExecution;
        }
    }

    package '03_Traceability' {

        doc /*
        Traceability summary:

        SF_001 IngestLegacyData:
        SYSR_001, SYSR_035

        SF_002 ExtractInformation:
        SYSR_002

        SF_003 NormalizeToCanonicalRepresentation:
        SYSR_003, SYSC_013

        SF_004 CreateNormalizedInformationUnits:
        SYSR_004, SYSR_005

        SF_005 AssessInformationQuality:
        SYSR_006

        SF_006 SupportControlledDataCompletion:
        SYSR_007

        SF_007 GenerateCandidateResults:
        SYSR_008, SYSR_009, SYSC_005, SYSC_006

        SF_008 CompareCandidateResults:
        SYSR_011, SYSR_012, SYSR_013

        SF_009 GenerateReviewReport:
        SYSR_010, SYSR_014, SYSR_018

        SF_010 CaptureHumanDecision:
        SYSR_015, SYSR_016, SYSR_017, SYSC_007

        SF_011 AlignTerminology:
        SYSR_019

        SF_012 DetectSemanticConflicts:
        SYSR_020

        SF_013 ApplyArchitectureConstraints:
        SYSR_021

        SF_014 GenerateSysMLv2Artifacts:
        SYSR_022, SYSR_024, SYSR_025, SYSR_026, SYSC_008, SYSC_009

        SF_015 MaintainInteractionAndInterfaceConsistency:
        SYSR_023

        SF_016 PrepareValidationWorkflow:
        SYSR_027, SYSR_028, SYSC_010

        SF_017 ProvideUserInteraction:
        SYSR_034, SYSR_035, SYSR_036, SYSR_037, SYSR_038, SYSR_039, SYSC_014, SYSC_015

        SF_018 SupportExtensiblePipelineExecution:
        SYSR_029, SYSR_030, SYSR_031, SYSR_032, SYSR_033, SYSC_001, SYSC_002, SYSC_003, SYSC_004, SYSC_011, SYSC_012

        Completeness check:
        All 39 system requirements SYSR_001 to SYSR_039 are covered.
        All 15 system design constraints SYSC_001 to SYSC_015 are covered.
        */
    }
       package '04_DetailedFunctionViews' {

        action dataPreparationDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_001 DataPreparationDetail

            Purpose:
            This detailed function view describes how heterogeneous legacy engineering data is transformed
            into processable, normalized and source traceable information units.

            Inputs:
            Machine readable legacy engineering artifact
            Upload metadata
            Optional user supplied completion information

            Outputs:
            Extracted content
            Canonical intermediate representation
            Normalized information units
            Source metadata
            Data quality assessment
            Optional completion request

            Included system functions:
            IngestLegacyData
            ExtractInformation
            NormalizeToCanonicalRepresentation
            CreateNormalizedInformationUnits
            AssessInformationQuality
            SupportControlledDataCompletion

            Functional flow:
            1. The user provides legacy engineering data.
            2. The system performs a basic check whether the artifact can be processed as machine readable input.
            3. The system extracts text, tables or structured content.
            4. The system normalizes extracted information into an internal canonical representation.
            5. The system splits the information into small, source traceable information units.
            6. The system assesses quality, completeness, consistency, relevance and reliability.
            7. If information is incomplete, controlled human supplied completion information can be requested.

            Decision points:
            Is the artifact machine readable?
            Could relevant information be extracted?
            Is the information sufficiently complete?
            Does the human need to provide missing information?
            May the information unit continue to the next pipeline phase?

            MVP relevance:
            Very high. This is the first real prototype section because it transforms external legacy files
            into an internal representation that can be processed further.

            Related requirements and constraints:
            SYSR_001
            SYSR_002
            SYSR_003
            SYSR_004
            SYSR_005
            SYSR_006
            SYSR_007
            SYSR_035
            SYSR_036
            SYSC_013
            */

            action ingestLegacyData : '00_FunctionDefinitions'::IngestLegacyData;
            action extractInformation : '00_FunctionDefinitions'::ExtractInformation;
            action normalizeToCanonicalRepresentation : '00_FunctionDefinitions'::NormalizeToCanonicalRepresentation;
            action createNormalizedInformationUnits : '00_FunctionDefinitions'::CreateNormalizedInformationUnits;
            action assessInformationQuality : '00_FunctionDefinitions'::AssessInformationQuality;
            action supportControlledDataCompletion : '00_FunctionDefinitions'::SupportControlledDataCompletion;
        }

        action candidateGenerationAndAssessmentDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_002 CandidateGenerationAndAssessmentDetail

            Purpose:
            This detailed function view describes how candidate results are generated, explained and compared
            based on normalized information units.

            Inputs:
            Normalized information units
            Data quality assessment
            Pipeline configuration
            Candidate generation configuration
            Optional technical vocabulary

            Outputs:
            Candidate results
            Candidate rationales
            Candidate comparison
            Detected differences
            Detected agreement

            Included system functions:
            AssessInformationQuality
            GenerateCandidateResults
            CompareCandidateResults

            Functional flow:
            1. The system receives assessed normalized information units.
            2. The system determines whether candidate generation is meaningful based on data quality.
            3. The system generates candidate results for selected processing tasks.
            4. The system generates rationales for the candidate results.
            5. The system compares candidates generated for the same task.
            6. The system marks differences and agreement as review information.

            Decision points:
            Is the information unit suitable for candidate generation?
            Are multiple candidate results available?
            Are there relevant differences between candidates?
            Are there stable agreements between candidates?
            Does the review need to highlight interpretation uncertainty?

            MVP relevance:
            Very high. This view describes the core value of the system because it turns normalized data into
            controlled candidate results instead of uncontrolled black box output.

            Related requirements and constraints:
            SYSR_006
            SYSR_008
            SYSR_009
            SYSR_010
            SYSR_011
            SYSR_012
            SYSR_013
            SYSC_005
            SYSC_006
            SYSC_007
            */

            action assessInformationQuality : '00_FunctionDefinitions'::AssessInformationQuality;
            action generateCandidateResults : '00_FunctionDefinitions'::GenerateCandidateResults;
            action compareCandidateResults : '00_FunctionDefinitions'::CompareCandidateResults;
        }

        action semanticAndArchitectureGuardrailsDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_003 SemanticAndArchitectureGuardrailsDetail

            Purpose:
            This detailed function view describes how semantic and architectural guardrails are applied to
            candidate results and later model structures.

            Inputs:
            Candidate results
            Technical vocabulary
            Ontology or semantic rules
            Architecture constraints
            Target model structure
            Interface related model expectations

            Outputs:
            Terminology alignment findings
            Semantic conflict findings
            Architecture constraint findings
            Interface consistency findings
            Guardrail feedback for review or synthesis

            Included system functions:
            AlignTerminology
            DetectSemanticConflicts
            ApplyArchitectureConstraints
            MaintainInteractionAndInterfaceConsistency

            Functional flow:
            1. The system aligns extracted or generated terms with a defined technical vocabulary.
            2. The system detects semantic conflicts or ambiguous term usage.
            3. The system checks candidate results against defined architecture constraints.
            4. The system checks whether generated interaction and interface structures remain consistent.
            5. The system provides findings to review or synthesis.

            Decision points:
            Can a term be assigned unambiguously?
            Are semantic conflicts present?
            Does a candidate violate architectural constraints?
            Are interface or interaction structures consistent?
            Does the human need to resolve a semantic or architectural issue?

            MVP relevance:
            Medium. This view is important for the target architecture, but only limited parts may be implemented
            in the MVP.

            Related requirements and constraints:
            SYSR_019
            SYSR_020
            SYSR_021
            SYSR_023
            SYSC_008
            SYSC_009
            SYSC_010
            */

            action alignTerminology : '00_FunctionDefinitions'::AlignTerminology;
            action detectSemanticConflicts : '00_FunctionDefinitions'::DetectSemanticConflicts;
            action applyArchitectureConstraints : '00_FunctionDefinitions'::ApplyArchitectureConstraints;
            action maintainInteractionAndInterfaceConsistency : '00_FunctionDefinitions'::MaintainInteractionAndInterfaceConsistency;
        }

        action humanReviewDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_004 HumanReviewDetail

            Purpose:
            This detailed function view describes the human in the loop mechanism. It ensures that candidate
            results are not used automatically without human review and approval.

            Inputs:
            Candidate results
            Candidate rationales
            Candidate comparison
            Detected differences
            Detected agreement
            Source references
            Guardrail findings

            Outputs:
            Review report
            Human decision
            Modified intermediate result
            Approved intermediate result
            Rejected candidate result
            Decision record

            Included system functions:
            GenerateReviewReport
            CaptureHumanDecision
            ProvideUserInteraction

            Functional flow:
            1. The system generates a review report.
            2. The system presents candidates, differences, agreement, sources and rationales.
            3. The human reviews the result.
            4. The human accepts, rejects or modifies the intermediate result.
            5. The system records the decision.
            6. Only accepted or modified results are used for subsequent processing steps.

            Decision points:
            Does the human accept the result?
            Does the human reject the result?
            Does the human modify the result?
            May the result be used as an intermediate result?
            Does a previous step need to be repeated?

            MVP relevance:
            Very high. This is a central argument of the thesis because AI supports the engineer but does not
            make the final modeling decision.

            Related requirements and constraints:
            SYSR_014
            SYSR_015
            SYSR_016
            SYSR_017
            SYSR_018
            SYSR_034
            SYSR_037
            SYSR_038
            SYSC_007
            SYSC_014
            SYSC_015
            */

            action generateReviewReport : '00_FunctionDefinitions'::GenerateReviewReport;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
        }

        action synthesisAndValidationDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_005 SynthesisAndValidationDetail

            Purpose:
            This detailed function view describes how approved intermediate results are transformed into
            SysML v2 artifacts and prepared for validation.

            Inputs:
            Approved intermediate results
            Target SysML v2 notation
            Target project structure
            Traceability information
            Validation configuration

            Outputs:
            Generated SysML v2 artifact
            Generated target project structure
            Traceability embedded in generated model
            Validation ready files
            Validation findings

            Included system functions:
            GenerateSysMLv2Artifacts
            PrepareValidationWorkflow

            Functional flow:
            1. The system receives human approved intermediate results.
            2. The system transforms the approved results into the defined SysML v2 target notation.
            3. The system generates files according to the defined target project structure.
            4. The system preserves traceability to the originating source information.
            5. The system provides artifacts for validation.
            6. The system may report validation findings to the user.

            Decision points:
            Is the intermediate result human approved?
            Is a suitable SysML v2 target structure defined?
            Can the model element be generated within the allowed SysML v2 subset?
            Are the generated artifacts validation ready?
            Are syntactic or structural findings present?

            MVP relevance:
            Very high. This view describes the visible output of the prototype.

            Related requirements and constraints:
            SYSR_022
            SYSR_024
            SYSR_025
            SYSR_026
            SYSR_027
            SYSR_028
            SYSR_039
            SYSC_008
            SYSC_009
            SYSC_010
            */

            action generateSysMLv2Artifacts : '00_FunctionDefinitions'::GenerateSysMLv2Artifacts;
            action prepareValidationWorkflow : '00_FunctionDefinitions'::PrepareValidationWorkflow;
        }

        action extensiblePipelineSupportDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_006 ExtensiblePipelineSupportDetail

            Purpose:
            This detailed function view describes the cross cutting capability that allows the MVP to be implemented
            as a modular and later extendable architectural core.

            Inputs:
            Pipeline configuration
            Selected processing capabilities
            Module interface definitions
            Execution state
            User interaction events

            Outputs:
            Configured pipeline execution
            Execution status
            Module handover information
            Error or status information
            Extensible processing structure

            Included system functions:
            SupportExtensiblePipelineExecution
            ProvideUserInteraction

            Functional flow:
            1. The system uses a defined pipeline configuration.
            2. The system determines which processing steps are active for the current run.
            3. The system coordinates execution, data handover and status information.
            4. The system separates control logic from task specific processing capabilities.
            5. The system allows later extension through additional processing capabilities.

            Decision points:
            Which pipeline steps are active?
            Which function receives which inputs?
            Has a processing step completed successfully?
            Does an error need to be reported to the user interface or review flow?
            Can a new capability be added through defined interfaces?

            MVP relevance:
            Very high, but mainly architectural. This view prevents the MVP from becoming a throwaway script.

            Related requirements and constraints:
            SYSR_029
            SYSR_030
            SYSR_031
            SYSR_032
            SYSR_033
            SYSC_001
            SYSC_002
            SYSC_003
            SYSC_004
            SYSC_011
            SYSC_012
            SYSC_014
            */

            action supportExtensiblePipelineExecution : '00_FunctionDefinitions'::SupportExtensiblePipelineExecution;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
        }
    } 
}