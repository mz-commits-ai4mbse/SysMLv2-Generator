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

    Architectural refinement:
    This version refines the workflow into an artifact based, recipe driven and human reviewed process.

    Main workflow principle:
    Raw legacy data is not directly transformed into model data.
    First, it is converted into a human readable ingestion artifact.
    Only after human review and approval is the content promoted into the approved input area.
    Candidate model data is then generated through recipe and context controlled execution.
    Candidate results may be produced through multiple agent personalities.
    Only after comparison, review and human approval are model data and SysML v2 artifacts generated.
    */

    package '00_FunctionDefinitions' {

        action def ExecuteTuringTransformationWorkflow {
            doc /*
            Main end to end system function.

            The function coordinates the transformation of machine readable legacy engineering data into
            generated SysML v2 artifacts through ingestion, artifact based review, approved input promotion,
            recipe based candidate generation, human review and artifact generation.

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

        action def GenerateIngestionArtifact {
            doc /*
            The system generates a human readable ingestion artifact from extracted legacy information.

            The ingestion artifact is intended for human review before the extracted content is promoted
            into the approved input area for further processing.

            Typical artifact type:
            Markdown report

            Derived from:
            SYSR_002 ExtractInformationFromLegacyArtifacts
            SYSR_004 PreserveSourceMetadata
            SYSR_014 GenerateReviewReport
            SYSR_018 ExplainModelingDecisions
            SYSR_036 PresentIngestionPreview
            */
        }

        action def ReviewIngestionArtifact {
            doc /*
            The system presents the generated ingestion artifact for human review.

            This creates the first explicit review gate in the workflow:
            Raw legacy data and extracted content are not used as approved input until the human review is completed.

            Derived from:
            SYSR_015 RequireHumanApproval
            SYSR_016 ProvideHumanDecisionOptions
            SYSR_017 RecordHumanDecision
            SYSR_036 PresentIngestionPreview
            SYSR_038 CaptureHumanReviewDecision
            SYSC_007 HumanApprovalIndependentOfCandidateAgreement
            */
        }

        action def PromoteApprovedInput {
            doc /*
            The system promotes human approved ingestion content into the approved input area.

            Only approved content may be used as input for downstream normalization, candidate generation
            and model synthesis.

            Derived from:
            SYSR_004 PreserveSourceMetadata
            SYSR_015 RequireHumanApproval
            SYSR_017 RecordHumanDecision
            SYSR_026 PreserveTraceabilityInGeneratedModel
            SYSR_030 SeparateControlFlowFromProcessingCapabilities
            SYSR_033 SupportConfigurablePipelineExecution
            */
        }

        action def NormalizeToCanonicalRepresentation {
            doc /*
            The system normalizes approved input information into an internal canonical representation.

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

        action def SelectRecipeAndContext {
            doc /*
            The system selects the recipe, required context artifacts and agent personalities required for a task.

            A recipe defines the task procedure, prompt structure, required context, expected outputs
            and review criteria.

            Context artifacts provide role definitions, modeling rules, target notation rules,
            project context and scope information.

            Agent personalities define role specific perspectives for candidate generation or review.

            Derived from:
            SYSR_009 SupportConfigurableCandidateGeneration
            SYSR_029 ProvideExtensibleProcessingStructure
            SYSR_030 SeparateControlFlowFromProcessingCapabilities
            SYSR_033 SupportConfigurablePipelineExecution
            SYSC_001 ModularPipelineArchitecture
            SYSC_002 CentralOrchestration
            SYSC_003 DefinedModuleInterfaces
            SYSC_012 OrchestratorControlledExecution
            */
        }

        action def GenerateCandidateResults {
            doc /*
            The system generates candidate results for selected processing tasks.

            The architecture may realize this through multiple configurable agent personalities or profiles,
            but this function describes the system capability rather than the concrete implementation.

            Derived from:
            SYSR_008 GenerateCandidateResults
            SYSR_009 SupportConfigurableCandidateGeneration
            SYSC_005 MultipleConfigurableAgentProfiles
            SYSC_006 ScalableAgentProfileCount
            */
        }

        action def ExecutePersonaBasedCandidateRuns {
            doc /*
            The system executes the selected task one or more times using selected agent personalities.

            Each run may produce an individual candidate artifact.
            The MVP may use one LLM backend with multiple agent personalities.
            The target architecture may allow multiple LLM backends or specialized agent implementations.

            Derived from:
            SYSR_008 GenerateCandidateResults
            SYSR_009 SupportConfigurableCandidateGeneration
            SYSR_011 CompareCandidateResults
            SYSR_012 PresentCandidateDifferences
            SYSR_013 PresentCandidateAgreement
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

        action def GenerateCandidateComparisonReport {
            doc /*
            The system generates a human readable comparison report from multiple candidate artifacts.

            The report presents candidate outputs, rationales, differences, agreement, uncertainties,
            source references and review questions.

            Typical artifact type:
            Markdown report

            Derived from:
            SYSR_010 GenerateCandidateRationales
            SYSR_011 CompareCandidateResults
            SYSR_012 PresentCandidateDifferences
            SYSR_013 PresentCandidateAgreement
            SYSR_014 GenerateReviewReport
            SYSR_018 ExplainModelingDecisions
            */
        }

        action def GenerateReviewReport {
            doc /*
            The system generates review reports that present candidate results, identified differences,
            rationales, source references and required human decisions.

            This function is retained as a generic review report capability.
            Specific review reports include ingestion artifact reports and candidate comparison reports.

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

        action def PromoteApprovedModelData {
            doc /*
            The system promotes human approved candidate or intermediate results into approved model data.

            Only approved model data may be used for SysML v2 artifact generation.

            Derived from:
            SYSR_015 RequireHumanApproval
            SYSR_016 ProvideHumanDecisionOptions
            SYSR_017 RecordHumanDecision
            SYSR_024 GenerateSysMLv2TargetNotation
            SYSR_026 PreserveTraceabilityInGeneratedModel
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

            1. Ingest raw legacy data.
            2. Extract information from legacy data.
            3. Generate a human readable ingestion artifact.
            4. Present the ingestion artifact for human review.
            5. Capture the human decision for the ingestion artifact.
            6. Promote approved content into the approved input area.
            7. Normalize approved input to a canonical representation.
            8. Create normalized information units.
            9. Assess information quality.
            10. Support controlled data completion if required.
            11. Select recipe, required context and agent personalities.
            12. Generate candidate results.
            13. Execute persona based candidate runs if configured.
            14. Compare candidate results.
            15. Generate a candidate comparison and review report.
            16. Capture the human decision for candidate or model data.
            17. Promote approved candidate output into approved model data.
            18. Align terminology if required by the selected pipeline configuration.
            19. Detect semantic conflicts if required by the selected pipeline configuration.
            20. Apply architecture constraints if required by the selected pipeline configuration.
            21. Generate SysML v2 artifacts from approved model data.
            22. Maintain interaction and interface consistency if required by the selected pipeline configuration.
            23. Prepare validation workflow.
            24. Provide user interaction throughout relevant workflow steps.
            25. Support extensible pipeline execution as cross cutting workflow capability.

            Review gates:
            Gate 1:
            Ingestion artifact review before content becomes approved input.

            Gate 2:
            Candidate comparison review before candidate output becomes approved model data.

            Note:
            The detailed control flow is intentionally documented as text in this transitional SysIDE model.
            A later CATIA model can represent the same sequence graphically as an activity or action flow.
            */

            action ingestLegacyData : '00_FunctionDefinitions'::IngestLegacyData;
            action extractInformation : '00_FunctionDefinitions'::ExtractInformation;
            action generateIngestionArtifact : '00_FunctionDefinitions'::GenerateIngestionArtifact;
            action reviewIngestionArtifact : '00_FunctionDefinitions'::ReviewIngestionArtifact;
            action captureHumanDecisionForIngestion : '00_FunctionDefinitions'::CaptureHumanDecision;
            action promoteApprovedInput : '00_FunctionDefinitions'::PromoteApprovedInput;
            action normalizeToCanonicalRepresentation : '00_FunctionDefinitions'::NormalizeToCanonicalRepresentation;
            action createNormalizedInformationUnits : '00_FunctionDefinitions'::CreateNormalizedInformationUnits;
            action assessInformationQuality : '00_FunctionDefinitions'::AssessInformationQuality;
            action supportControlledDataCompletion : '00_FunctionDefinitions'::SupportControlledDataCompletion;
            action selectRecipeAndContext : '00_FunctionDefinitions'::SelectRecipeAndContext;
            action generateCandidateResults : '00_FunctionDefinitions'::GenerateCandidateResults;
            action executePersonaBasedCandidateRuns : '00_FunctionDefinitions'::ExecutePersonaBasedCandidateRuns;
            action compareCandidateResults : '00_FunctionDefinitions'::CompareCandidateResults;
            action generateCandidateComparisonReport : '00_FunctionDefinitions'::GenerateCandidateComparisonReport;
            action captureHumanDecisionForCandidates : '00_FunctionDefinitions'::CaptureHumanDecision;
            action promoteApprovedModelData : '00_FunctionDefinitions'::PromoteApprovedModelData;
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

        action dataPreparationAndIngestionReview : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Data preparation and ingestion review groups the functions required to transform raw legacy artifacts
            into reviewed and approved input for downstream processing.

            Included functions:
            IngestLegacyData
            ExtractInformation
            GenerateIngestionArtifact
            ReviewIngestionArtifact
            CaptureHumanDecision
            PromoteApprovedInput
            NormalizeToCanonicalRepresentation
            CreateNormalizedInformationUnits
            AssessInformationQuality
            SupportControlledDataCompletion
            */

            action ingestLegacyData : '00_FunctionDefinitions'::IngestLegacyData;
            action extractInformation : '00_FunctionDefinitions'::ExtractInformation;
            action generateIngestionArtifact : '00_FunctionDefinitions'::GenerateIngestionArtifact;
            action reviewIngestionArtifact : '00_FunctionDefinitions'::ReviewIngestionArtifact;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action promoteApprovedInput : '00_FunctionDefinitions'::PromoteApprovedInput;
            action normalizeToCanonicalRepresentation : '00_FunctionDefinitions'::NormalizeToCanonicalRepresentation;
            action createNormalizedInformationUnits : '00_FunctionDefinitions'::CreateNormalizedInformationUnits;
            action assessInformationQuality : '00_FunctionDefinitions'::AssessInformationQuality;
            action supportControlledDataCompletion : '00_FunctionDefinitions'::SupportControlledDataCompletion;
        }

        action recipeDrivenCandidateGenerationAndAssessment : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Recipe driven candidate generation and assessment groups the functions required to select recipes,
            load context, execute persona based candidate runs and compare candidate outputs for review.

            Included functions:
            SelectRecipeAndContext
            GenerateCandidateResults
            ExecutePersonaBasedCandidateRuns
            CompareCandidateResults
            GenerateCandidateComparisonReport
            */

            action selectRecipeAndContext : '00_FunctionDefinitions'::SelectRecipeAndContext;
            action generateCandidateResults : '00_FunctionDefinitions'::GenerateCandidateResults;
            action executePersonaBasedCandidateRuns : '00_FunctionDefinitions'::ExecutePersonaBasedCandidateRuns;
            action compareCandidateResults : '00_FunctionDefinitions'::CompareCandidateResults;
            action generateCandidateComparisonReport : '00_FunctionDefinitions'::GenerateCandidateComparisonReport;
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

        action humanReviewAndApprovalGates : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Human review and approval gates group the functions required to make ingestion artifacts,
            candidate artifacts and model data understandable and controllable by the human reviewer.

            Included functions:
            GenerateIngestionArtifact
            ReviewIngestionArtifact
            GenerateCandidateComparisonReport
            GenerateReviewReport
            CaptureHumanDecision
            PromoteApprovedInput
            PromoteApprovedModelData
            ProvideUserInteraction
            */

            action generateIngestionArtifact : '00_FunctionDefinitions'::GenerateIngestionArtifact;
            action reviewIngestionArtifact : '00_FunctionDefinitions'::ReviewIngestionArtifact;
            action generateCandidateComparisonReport : '00_FunctionDefinitions'::GenerateCandidateComparisonReport;
            action generateReviewReport : '00_FunctionDefinitions'::GenerateReviewReport;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action promoteApprovedInput : '00_FunctionDefinitions'::PromoteApprovedInput;
            action promoteApprovedModelData : '00_FunctionDefinitions'::PromoteApprovedModelData;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
        }

        action synthesisAndValidation : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Synthesis and validation groups the functions required to generate SysML v2 artifacts from
            approved model data and prepare them for validation.

            Included functions:
            PromoteApprovedModelData
            GenerateSysMLv2Artifacts
            PrepareValidationWorkflow
            */

            action promoteApprovedModelData : '00_FunctionDefinitions'::PromoteApprovedModelData;
            action generateSysMLv2Artifacts : '00_FunctionDefinitions'::GenerateSysMLv2Artifacts;
            action prepareValidationWorkflow : '00_FunctionDefinitions'::PrepareValidationWorkflow;
        }

        action extensiblePipelineSupport : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            Detail view candidate:
            Extensible pipeline support groups the cross cutting capability that enables the MVP to be implemented
            as a selected subset of the later target architecture.

            Included functions:
            SelectRecipeAndContext
            SupportExtensiblePipelineExecution
            ProvideUserInteraction
            */

            action selectRecipeAndContext : '00_FunctionDefinitions'::SelectRecipeAndContext;
            action supportExtensiblePipelineExecution : '00_FunctionDefinitions'::SupportExtensiblePipelineExecution;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
        }
    }

    package '03_Traceability' {

        doc /*
        Traceability summary:

        SF_001 IngestLegacyData:
        SYSR_001, SYSR_035

        SF_002 ExtractInformation:
        SYSR_002

        SF_003 GenerateIngestionArtifact:
        SYSR_002, SYSR_004, SYSR_014, SYSR_018, SYSR_036

        SF_004 ReviewIngestionArtifact:
        SYSR_015, SYSR_016, SYSR_017, SYSR_036, SYSR_038, SYSC_007

        SF_005 PromoteApprovedInput:
        SYSR_004, SYSR_015, SYSR_017, SYSR_026, SYSR_030, SYSR_033

        SF_006 NormalizeToCanonicalRepresentation:
        SYSR_003, SYSC_013

        SF_007 CreateNormalizedInformationUnits:
        SYSR_004, SYSR_005

        SF_008 AssessInformationQuality:
        SYSR_006

        SF_009 SupportControlledDataCompletion:
        SYSR_007

        SF_010 SelectRecipeAndContext:
        SYSR_009, SYSR_029, SYSR_030, SYSR_033, SYSC_001, SYSC_002, SYSC_003, SYSC_012

        SF_011 GenerateCandidateResults:
        SYSR_008, SYSR_009, SYSC_005, SYSC_006

        SF_012 ExecutePersonaBasedCandidateRuns:
        SYSR_008, SYSR_009, SYSR_011, SYSR_012, SYSR_013, SYSC_005, SYSC_006

        SF_013 CompareCandidateResults:
        SYSR_011, SYSR_012, SYSR_013

        SF_014 GenerateCandidateComparisonReport:
        SYSR_010, SYSR_011, SYSR_012, SYSR_013, SYSR_014, SYSR_018

        SF_015 GenerateReviewReport:
        SYSR_010, SYSR_014, SYSR_018

        SF_016 CaptureHumanDecision:
        SYSR_015, SYSR_016, SYSR_017, SYSC_007

        SF_017 PromoteApprovedModelData:
        SYSR_015, SYSR_016, SYSR_017, SYSR_024, SYSR_026

        SF_018 AlignTerminology:
        SYSR_019

        SF_019 DetectSemanticConflicts:
        SYSR_020

        SF_020 ApplyArchitectureConstraints:
        SYSR_021

        SF_021 GenerateSysMLv2Artifacts:
        SYSR_022, SYSR_024, SYSR_025, SYSR_026, SYSC_008, SYSC_009

        SF_022 MaintainInteractionAndInterfaceConsistency:
        SYSR_023

        SF_023 PrepareValidationWorkflow:
        SYSR_027, SYSR_028, SYSC_010

        SF_024 ProvideUserInteraction:
        SYSR_034, SYSR_035, SYSR_036, SYSR_037, SYSR_038, SYSR_039, SYSC_014, SYSC_015

        SF_025 SupportExtensiblePipelineExecution:
        SYSR_029, SYSR_030, SYSR_031, SYSR_032, SYSR_033, SYSC_001, SYSC_002, SYSC_003, SYSC_004, SYSC_011, SYSC_012

        Completeness check:
        All 39 system requirements SYSR_001 to SYSR_039 are covered.
        All 15 system design constraints SYSC_001 to SYSC_015 are covered.

        Workflow refinement check:
        The functional model now includes explicit artifact based workflow steps,
        explicit ingestion review gate,
        explicit candidate comparison review gate,
        recipe and context selection,
        persona based candidate execution,
        approved input promotion and approved model data promotion.
        */
    }

    package '04_DetailedFunctionViews' {

        action dataPreparationDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_001 DataPreparationDetail

            Purpose:
            This detailed function view describes how heterogeneous legacy engineering data is transformed
            into a human readable ingestion artifact, reviewed by the human and then promoted into approved input
            for downstream processing.

            Inputs:
            Raw machine readable legacy engineering artifact
            Upload metadata
            Optional user supplied completion information

            Outputs:
            Extracted content
            Human readable ingestion artifact
            Human decision for ingestion artifact
            Approved input
            Canonical intermediate representation
            Normalized information units
            Source metadata
            Data quality assessment
            Optional completion request

            Included system functions:
            IngestLegacyData
            ExtractInformation
            GenerateIngestionArtifact
            ReviewIngestionArtifact
            CaptureHumanDecision
            PromoteApprovedInput
            NormalizeToCanonicalRepresentation
            CreateNormalizedInformationUnits
            AssessInformationQuality
            SupportControlledDataCompletion

            Functional flow:
            1. The user provides raw legacy engineering data.
            2. The system performs a basic check whether the artifact can be processed as machine readable input.
            3. The system extracts text, tables or structured content.
            4. The system generates a human readable ingestion artifact.
            5. The human reviews the ingestion artifact.
            6. The system captures the human decision.
            7. Approved content is promoted into the approved input area.
            8. The system normalizes approved input into an internal canonical representation.
            9. The system splits the information into small, source traceable information units.
            10. The system assesses quality, completeness, consistency, relevance and reliability.
            11. If information is incomplete, controlled human supplied completion information can be requested.

            Decision points:
            Is the artifact machine readable?
            Could relevant information be extracted?
            Is the ingestion artifact understandable and traceable?
            Does the human approve, reject or modify the ingestion artifact?
            May the content be promoted into approved input?
            Is the approved input sufficiently complete?
            Does the human need to provide missing information?
            May the information unit continue to the next pipeline phase?

            MVP relevance:
            Very high. This is the first real prototype section because it transforms external legacy files
            into reviewed and approved input before any model candidate is generated.

            Related requirements and constraints:
            SYSR_001
            SYSR_002
            SYSR_003
            SYSR_004
            SYSR_005
            SYSR_006
            SYSR_007
            SYSR_014
            SYSR_015
            SYSR_016
            SYSR_017
            SYSR_035
            SYSR_036
            SYSR_038
            SYSC_007
            SYSC_013
            */

            action ingestLegacyData : '00_FunctionDefinitions'::IngestLegacyData;
            action extractInformation : '00_FunctionDefinitions'::ExtractInformation;
            action generateIngestionArtifact : '00_FunctionDefinitions'::GenerateIngestionArtifact;
            action reviewIngestionArtifact : '00_FunctionDefinitions'::ReviewIngestionArtifact;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action promoteApprovedInput : '00_FunctionDefinitions'::PromoteApprovedInput;
            action normalizeToCanonicalRepresentation : '00_FunctionDefinitions'::NormalizeToCanonicalRepresentation;
            action createNormalizedInformationUnits : '00_FunctionDefinitions'::CreateNormalizedInformationUnits;
            action assessInformationQuality : '00_FunctionDefinitions'::AssessInformationQuality;
            action supportControlledDataCompletion : '00_FunctionDefinitions'::SupportControlledDataCompletion;
        }

        action recipeDrivenCandidateGenerationDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_002 RecipeDrivenCandidateGenerationDetail

            Purpose:
            This detailed function view describes how recipes, context artifacts and agent personalities are selected
            and used to generate one or more candidate artifacts.

            Inputs:
            Approved input
            Normalized information units
            Data quality assessment
            Task specification
            Recipe artifact
            Context artifacts
            Agent personality artifacts
            Pipeline configuration
            Candidate generation configuration

            Outputs:
            Selected recipe
            Loaded context package
            Selected agent personalities
            Candidate run artifacts
            Candidate results
            Candidate rationales

            Included system functions:
            SelectRecipeAndContext
            GenerateCandidateResults
            ExecutePersonaBasedCandidateRuns

            Functional flow:
            1. The system receives approved and normalized input.
            2. The system identifies the required task type.
            3. The system selects the corresponding recipe.
            4. The system loads required context artifacts and agent personalities.
            5. The system builds the task specific prompt from recipe, context and input artifacts.
            6. The system executes the candidate generation task.
            7. If configured, the same task is executed multiple times with different agent personalities.
            8. Each run produces a candidate artifact.

            Decision points:
            Which recipe matches the task?
            Which context artifacts are required?
            Which agent personalities are selected?
            Is one candidate run sufficient?
            Should the task be executed with multiple personalities?
            Did each candidate run produce a usable artifact?

            MVP relevance:
            Very high. This view describes the recipe based orchestration principle of the MVP.

            Related requirements and constraints:
            SYSR_008
            SYSR_009
            SYSR_011
            SYSR_012
            SYSR_013
            SYSR_029
            SYSR_030
            SYSR_033
            SYSC_001
            SYSC_002
            SYSC_003
            SYSC_005
            SYSC_006
            SYSC_012
            */

            action selectRecipeAndContext : '00_FunctionDefinitions'::SelectRecipeAndContext;
            action generateCandidateResults : '00_FunctionDefinitions'::GenerateCandidateResults;
            action executePersonaBasedCandidateRuns : '00_FunctionDefinitions'::ExecutePersonaBasedCandidateRuns;
        }

        action candidateComparisonAndReviewDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_003 CandidateComparisonAndReviewDetail

            Purpose:
            This detailed function view describes how candidate artifacts are compared and turned into a
            human readable comparison and review artifact.

            Inputs:
            Candidate artifacts
            Candidate rationales
            Source references
            Agent personality metadata
            Recipe metadata
            Traceability information

            Outputs:
            Candidate comparison
            Detected differences
            Detected agreement
            Candidate comparison report
            Review questions
            Human decision
            Approved model data

            Included system functions:
            CompareCandidateResults
            GenerateCandidateComparisonReport
            GenerateReviewReport
            CaptureHumanDecision
            PromoteApprovedModelData
            ProvideUserInteraction

            Functional flow:
            1. The system collects candidate artifacts created for the same task.
            2. The system compares candidate outputs.
            3. The system identifies differences, agreement and uncertainty.
            4. The system generates a human readable candidate comparison report.
            5. The report is presented to the human reviewer.
            6. The human accepts, rejects or modifies the candidate output.
            7. The system records the decision.
            8. Approved or modified output is promoted into approved model data.

            Decision points:
            Are multiple candidate artifacts available?
            Are there relevant differences between candidates?
            Are there stable agreements between candidates?
            Does the report explain the differences and rationales sufficiently?
            Does the human accept, reject or modify the candidate output?
            May the output be promoted into approved model data?

            MVP relevance:
            Very high. This is the central human in the loop gate before model data is generated.

            Related requirements and constraints:
            SYSR_010
            SYSR_011
            SYSR_012
            SYSR_013
            SYSR_014
            SYSR_015
            SYSR_016
            SYSR_017
            SYSR_018
            SYSR_037
            SYSR_038
            SYSC_007
            SYSC_014
            SYSC_015
            */

            action compareCandidateResults : '00_FunctionDefinitions'::CompareCandidateResults;
            action generateCandidateComparisonReport : '00_FunctionDefinitions'::GenerateCandidateComparisonReport;
            action generateReviewReport : '00_FunctionDefinitions'::GenerateReviewReport;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action promoteApprovedModelData : '00_FunctionDefinitions'::PromoteApprovedModelData;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
        }

        action semanticAndArchitectureGuardrailsDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_004 SemanticAndArchitectureGuardrailsDetail

            Purpose:
            This detailed function view describes how semantic and architectural guardrails are applied to
            candidate results and later model structures.

            Inputs:
            Candidate results
            Approved model data
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
            3. The system checks candidate results or approved model data against defined architecture constraints.
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

        action synthesisAndValidationDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_005 SynthesisAndValidationDetail

            Purpose:
            This detailed function view describes how approved model data is transformed into SysML v2 artifacts
            and prepared for validation.

            Inputs:
            Approved model data
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
            PromoteApprovedModelData
            GenerateSysMLv2Artifacts
            PrepareValidationWorkflow

            Functional flow:
            1. The system receives approved model data.
            2. The system transforms the approved model data into the defined SysML v2 target notation.
            3. The system generates files according to the defined target project structure.
            4. The system preserves traceability to the originating source information, recipe, candidate runs and human decisions.
            5. The system provides artifacts for validation.
            6. The system may report validation findings to the user.

            Decision points:
            Is the model data human approved?
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

            action promoteApprovedModelData : '00_FunctionDefinitions'::PromoteApprovedModelData;
            action generateSysMLv2Artifacts : '00_FunctionDefinitions'::GenerateSysMLv2Artifacts;
            action prepareValidationWorkflow : '00_FunctionDefinitions'::PrepareValidationWorkflow;
        }

        action extensiblePipelineSupportDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_006 ExtensiblePipelineSupportDetail

            Purpose:
            This detailed function view describes the cross cutting capability that allows the MVP to be implemented
            as a modular, recipe driven and later extendable architectural core.

            Inputs:
            Pipeline configuration
            Selected processing capabilities
            Recipe artifacts
            Context artifacts
            Agent personality artifacts
            Module interface definitions
            Execution state
            User interaction events

            Outputs:
            Configured pipeline execution
            Selected recipe and context package
            Execution status
            Module handover information
            Error or status information
            Extensible processing structure

            Included system functions:
            SelectRecipeAndContext
            SupportExtensiblePipelineExecution
            ProvideUserInteraction

            Functional flow:
            1. The system uses a defined pipeline configuration.
            2. The system determines which processing steps are active for the current run.
            3. The system selects recipes, context artifacts and agent personalities.
            4. The system coordinates execution, data handover and status information.
            5. The system separates control logic from task specific processing capabilities.
            6. The system allows later extension through additional processing capabilities.

            Decision points:
            Which pipeline steps are active?
            Which recipe is selected?
            Which context artifacts are required?
            Which function receives which inputs?
            Has a processing step completed successfully?
            Does an error need to be reported to the user interface or review flow?
            Can a new capability be added through defined interfaces?

            MVP relevance:
            Very high, but mainly architectural. This view prevents the MVP from becoming a throwaway script.

            Related requirements and constraints:
            SYSR_009
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

            action selectRecipeAndContext : '00_FunctionDefinitions'::SelectRecipeAndContext;
            action supportExtensiblePipelineExecution : '00_FunctionDefinitions'::SupportExtensiblePipelineExecution;
            action provideUserInteraction : '00_FunctionDefinitions'::ProvideUserInteraction;
        }

        action artifactBasedReviewWorkflowDetail : '00_FunctionDefinitions'::ExecuteTuringTransformationWorkflow {
            doc /*
            View ID:
            SFV_007 ArtifactBasedReviewWorkflowDetail

            Purpose:
            This detailed function view summarizes the artifact based review workflow of the MVP.

            It makes explicit that raw data, candidate data and model data are separated by human review gates.

            Artifact states:
            Raw legacy data
            Human readable ingestion artifact
            Approved input
            Candidate artifacts
            Candidate comparison report
            Approved model data
            Generated SysML v2 artifacts

            Functional flow:
            1. Raw legacy data is ingested.
            2. A human readable ingestion artifact is generated.
            3. The ingestion artifact is reviewed by the human.
            4. Approved content is promoted into approved input.
            5. Candidate artifacts are generated from approved input using recipes, context and agent personalities.
            6. Candidate artifacts are compared.
            7. A candidate comparison report is reviewed by the human.
            8. Approved candidate output is promoted into approved model data.
            9. SysML v2 artifacts are generated from approved model data.

            Review gate 1:
            Ingestion artifact to approved input.

            Review gate 2:
            Candidate comparison report to approved model data.

            MVP relevance:
            Very high. This view captures the central control and assurance mechanism of the MVP.

            Related requirements and constraints:
            SYSR_014
            SYSR_015
            SYSR_016
            SYSR_017
            SYSR_018
            SYSR_026
            SYSR_036
            SYSR_037
            SYSR_038
            SYSC_007
            SYSC_014
            SYSC_015
            */

            action generateIngestionArtifact : '00_FunctionDefinitions'::GenerateIngestionArtifact;
            action reviewIngestionArtifact : '00_FunctionDefinitions'::ReviewIngestionArtifact;
            action promoteApprovedInput : '00_FunctionDefinitions'::PromoteApprovedInput;
            action executePersonaBasedCandidateRuns : '00_FunctionDefinitions'::ExecutePersonaBasedCandidateRuns;
            action generateCandidateComparisonReport : '00_FunctionDefinitions'::GenerateCandidateComparisonReport;
            action captureHumanDecision : '00_FunctionDefinitions'::CaptureHumanDecision;
            action promoteApprovedModelData : '00_FunctionDefinitions'::PromoteApprovedModelData;
            action generateSysMLv2Artifacts : '00_FunctionDefinitions'::GenerateSysMLv2Artifacts;
        }
    }
}
