package Turing_System_Logical {

    doc /*
    Purpose:
    This package documents the logical system architecture of the Turing Generator.

    Modeling status:
    Transitional SysIDE shadow model.

    Modeling decision:
    The target product and the MVP use the same logical component definitions.
    The MVP is modeled as a reduced and partially realized configuration of the target logical architecture.
    MVP components are not modeled as alternative replacement components.

    Scope:
    This package describes logical components, logical data objects, architecture configurations,
    target to MVP mapping, function allocation and traceability.

    Physical realization and Python implementation are intentionally not modeled here.
    */

    package '00_LogicalDefinitions' {

        part def LogicalComponent {
            doc /*
            Base type for logical components of the Turing Generator.
            */
        }

        part def UserInteractionComponent :> LogicalComponent {
            doc /*
            Provides user interaction capabilities for upload, preview, review, decision capture
            and access to generated SysML v2 artifacts.
            */
        }

        part def PipelineOrchestrationComponent :> LogicalComponent {
            doc /*
            Coordinates the execution of selected pipeline capabilities, manages control flow,
            data handover, execution state and error or status information.
            */
        }

        part def LegacyDataIngestionComponent :> LogicalComponent {
            doc /*
            Receives machine readable legacy engineering artifacts and prepares them for extraction.
            */
        }

        part def InformationExtractionComponent :> LogicalComponent {
            doc /*
            Extracts text, tables or structured content from ingested legacy engineering artifacts.
            */
        }

        part def CanonicalRepresentationComponent :> LogicalComponent {
            doc /*
            Converts extracted information into an internal canonical representation.
            */
        }

        part def InformationUnitManagementComponent :> LogicalComponent {
            doc /*
            Creates bounded, source traceable normalized information units from canonical information.
            */
        }

        part def InformationQualityAssessmentComponent :> LogicalComponent {
            doc /*
            Assesses normalized information units for completeness, consistency, machine readability,
            relevance and reliability.
            */
        }

        part def ControlledDataCompletionComponent :> LogicalComponent {
            doc /*
            Supports controlled completion of incomplete legacy data using human supplied information.
            */
        }

        part def CandidateGenerationComponent :> LogicalComponent {
            doc /*
            Generates candidate results for selected processing tasks.
            */
        }

        part def AgentProfileManagementComponent :> LogicalComponent {
            doc /*
            Manages configurable agent profiles used during candidate generation.
            */
        }

        part def CandidateComparisonComponent :> LogicalComponent {
            doc /*
            Compares candidate results generated for the same processing task and identifies
            differences and agreement.
            */
        }

        part def ReviewReportingComponent :> LogicalComponent {
            doc /*
            Generates review reports containing candidate results, rationales, differences,
            agreement, source references and required human decisions.
            */
        }

        part def HumanDecisionManagementComponent :> LogicalComponent {
            doc /*
            Captures, records and provides human decisions for accepted, rejected or modified
            intermediate results.
            */
        }

        part def TerminologyAlignmentComponent :> LogicalComponent {
            doc /*
            Aligns extracted or generated terms with a defined technical vocabulary.
            */
        }

        part def SemanticConflictDetectionComponent :> LogicalComponent {
            doc /*
            Detects ontology or vocabulary conflicts in candidate results or model structures.
            */
        }

        part def ArchitectureConstraintEvaluationComponent :> LogicalComponent {
            doc /*
            Evaluates candidate results and generated structures against defined architectural constraints.
            */
        }

        part def SysMLv2SynthesisComponent :> LogicalComponent {
            doc /*
            Generates SysML v2 textual artifacts according to a defined target notation and
            target project structure.
            */
        }

        part def InteractionAndInterfaceConsistencyComponent :> LogicalComponent {
            doc /*
            Maintains consistency of generated interaction and interface related model elements.
            */
        }

        part def ValidationPreparationComponent :> LogicalComponent {
            doc /*
            Prepares generated SysML v2 artifacts for validation by the selected validation environment
            and may report validation findings.
            */
        }

        part def TraceabilityManagementComponent :> LogicalComponent {
            doc /*
            Preserves traceability between source information, intermediate results, human decisions,
            generated SysML v2 artifacts and validation findings.
            */
        }

        item def LegacyEngineeringArtifact {
            doc /*
            Machine readable input artifact provided as legacy engineering data.
            */
        }

        item def ExtractedContent {
            doc /*
            Text, table or structured content extracted from a legacy engineering artifact.
            */
        }

        item def CanonicalIntermediateRepresentation {
            doc /*
            Internal normalized representation used between processing steps.
            In the MVP this is expected to be JSON based.
            */
        }

        item def NormalizedInformationUnit {
            doc /*
            Bounded and source traceable portion of normalized information.
            */
        }

        item def CandidateResult {
            doc /*
            Generated candidate output for a selected processing task before human approval.
            */
        }

        item def CandidateComparison {
            doc /*
            Review information describing differences and agreement between candidate results.
            */
        }

        item def ReviewReport {
            doc /*
            Review artifact containing candidates, rationales, source references, differences,
            agreement and required human decisions.
            */
        }

        item def HumanDecisionRecord {
            doc /*
            Record of a human decision for an intermediate result.
            */
        }

        item def ApprovedIntermediateResult {
            doc /*
            Human approved or human modified result that may be used by subsequent processing steps.
            */
        }

        item def SysMLv2Artifact {
            doc /*
            Generated textual SysML v2 artifact.
            */
        }

        item def ValidationFinding {
            doc /*
            Syntactic or structural finding produced by the validation workflow.
            */
        }
    }

    package '01_TargetLogicalArchitecture' {

        part def TargetLogicalArchitecture {
            doc /*
            Logical architecture configuration of the intended target product.

            This architecture includes all logical components required to cover the full set of
            system requirements and system design constraints.
            */

            part userInteraction : '00_LogicalDefinitions'::UserInteractionComponent;
            part pipelineOrchestration : '00_LogicalDefinitions'::PipelineOrchestrationComponent;
            part legacyDataIngestion : '00_LogicalDefinitions'::LegacyDataIngestionComponent;
            part informationExtraction : '00_LogicalDefinitions'::InformationExtractionComponent;
            part canonicalRepresentation : '00_LogicalDefinitions'::CanonicalRepresentationComponent;
            part informationUnitManagement : '00_LogicalDefinitions'::InformationUnitManagementComponent;
            part informationQualityAssessment : '00_LogicalDefinitions'::InformationQualityAssessmentComponent;
            part controlledDataCompletion : '00_LogicalDefinitions'::ControlledDataCompletionComponent;
            part candidateGeneration : '00_LogicalDefinitions'::CandidateGenerationComponent;
            part agentProfileManagement : '00_LogicalDefinitions'::AgentProfileManagementComponent;
            part candidateComparison : '00_LogicalDefinitions'::CandidateComparisonComponent;
            part reviewReporting : '00_LogicalDefinitions'::ReviewReportingComponent;
            part humanDecisionManagement : '00_LogicalDefinitions'::HumanDecisionManagementComponent;
            part terminologyAlignment : '00_LogicalDefinitions'::TerminologyAlignmentComponent;
            part semanticConflictDetection : '00_LogicalDefinitions'::SemanticConflictDetectionComponent;
            part architectureConstraintEvaluation : '00_LogicalDefinitions'::ArchitectureConstraintEvaluationComponent;
            part sysMLv2Synthesis : '00_LogicalDefinitions'::SysMLv2SynthesisComponent;
            part interactionAndInterfaceConsistency : '00_LogicalDefinitions'::InteractionAndInterfaceConsistencyComponent;
            part validationPreparation : '00_LogicalDefinitions'::ValidationPreparationComponent;
            part traceabilityManagement : '00_LogicalDefinitions'::TraceabilityManagementComponent;
        }

        part targetLogicalArchitecture : TargetLogicalArchitecture;
    }

    package '02_MVPLogicalArchitecture' {

        part def MVPLogicalArchitecture {
            doc /*
            Logical architecture configuration of the MVP.

            The MVP uses the same logical component definitions as the target product.
            It represents a reduced and partially realized subset of the target architecture.

            Included or partially included MVP scope:
            User interaction for upload, preview, review, decision capture and artifact access.
            Pipeline orchestration for the selected MVP processing flow.
            Legacy data ingestion.
            Information extraction.
            Canonical JSON based intermediate representation.
            Normalized information unit creation.
            Basic information quality assessment.
            Candidate generation using configurable profiles.
            Candidate comparison.
            Review report generation.
            Human decision capture.
            SysML v2 artifact generation for a limited target notation subset.
            Validation preparation for the selected validation environment.
            Traceability preservation.

            Not fully implemented in MVP:
            Controlled data completion.
            Terminology alignment.
            Semantic conflict detection.
            Full architecture constraint evaluation.
            Interaction and interface consistency management.
            Full validation finding feedback loop.
            */

            part userInteraction : '00_LogicalDefinitions'::UserInteractionComponent;
            part pipelineOrchestration : '00_LogicalDefinitions'::PipelineOrchestrationComponent;
            part legacyDataIngestion : '00_LogicalDefinitions'::LegacyDataIngestionComponent;
            part informationExtraction : '00_LogicalDefinitions'::InformationExtractionComponent;
            part canonicalRepresentation : '00_LogicalDefinitions'::CanonicalRepresentationComponent;
            part informationUnitManagement : '00_LogicalDefinitions'::InformationUnitManagementComponent;
            part informationQualityAssessment : '00_LogicalDefinitions'::InformationQualityAssessmentComponent;
            part candidateGeneration : '00_LogicalDefinitions'::CandidateGenerationComponent;
            part agentProfileManagement : '00_LogicalDefinitions'::AgentProfileManagementComponent;
            part candidateComparison : '00_LogicalDefinitions'::CandidateComparisonComponent;
            part reviewReporting : '00_LogicalDefinitions'::ReviewReportingComponent;
            part humanDecisionManagement : '00_LogicalDefinitions'::HumanDecisionManagementComponent;
            part architectureConstraintEvaluation : '00_LogicalDefinitions'::ArchitectureConstraintEvaluationComponent;
            part sysMLv2Synthesis : '00_LogicalDefinitions'::SysMLv2SynthesisComponent;
            part validationPreparation : '00_LogicalDefinitions'::ValidationPreparationComponent;
            part traceabilityManagement : '00_LogicalDefinitions'::TraceabilityManagementComponent;
        }

        part mvpLogicalArchitecture : MVPLogicalArchitecture;
    }

    package '03_TargetToMVPMapping' {

        doc /*
        Target to MVP mapping:

        LC_001 UserInteractionComponent:
        Target status: included
        MVP status: partially implemented
        MVP scope: upload, ingestion preview, review report display, human decision capture, artifact access

        LC_002 PipelineOrchestrationComponent:
        Target status: included
        MVP status: implemented
        MVP scope: selected processing flow, data handover, execution state, error and status information

        LC_003 LegacyDataIngestionComponent:
        Target status: included
        MVP status: implemented
        MVP scope: selected machine readable legacy file formats

        LC_004 InformationExtractionComponent:
        Target status: included
        MVP status: implemented
        MVP scope: extraction of text, tables or structured content from selected input formats

        LC_005 CanonicalRepresentationComponent:
        Target status: included
        MVP status: implemented
        MVP scope: JSON based canonical intermediate representation

        LC_006 InformationUnitManagementComponent:
        Target status: included
        MVP status: implemented
        MVP scope: creation of bounded, source traceable information units

        LC_007 InformationQualityAssessmentComponent:
        Target status: included
        MVP status: partially implemented
        MVP scope: basic completeness, consistency, readability, relevance and reliability assessment

        LC_008 ControlledDataCompletionComponent:
        Target status: included
        MVP status: not implemented or only documented as extension point
        Reason: target function, not required for first executable MVP

        LC_009 CandidateGenerationComponent:
        Target status: included
        MVP status: implemented
        MVP scope: candidate generation for selected processing tasks

        LC_010 AgentProfileManagementComponent:
        Target status: included
        MVP status: partially implemented
        MVP scope: limited configurable agent profiles

        LC_011 CandidateComparisonComponent:
        Target status: included
        MVP status: implemented
        MVP scope: candidate comparison with differences and agreement as review information

        LC_012 ReviewReportingComponent:
        Target status: included
        MVP status: implemented
        MVP scope: review report for candidates, rationales, source references and decisions

        LC_013 HumanDecisionManagementComponent:
        Target status: included
        MVP status: implemented
        MVP scope: accept, reject or modify intermediate results

        LC_014 TerminologyAlignmentComponent:
        Target status: included
        MVP status: not implemented or only stubbed
        Reason: target function, may be added after MVP

        LC_015 SemanticConflictDetectionComponent:
        Target status: included
        MVP status: not implemented or only stubbed
        Reason: target function, may be added after MVP

        LC_016 ArchitectureConstraintEvaluationComponent:
        Target status: included
        MVP status: partially implemented or only documented as extension point
        MVP scope: limited target notation and project structure constraints

        LC_017 SysMLv2SynthesisComponent:
        Target status: included
        MVP status: implemented
        MVP scope: generation of selected valid SysML v2 textual artifacts

        LC_018 InteractionAndInterfaceConsistencyComponent:
        Target status: included
        MVP status: not implemented
        Reason: post MVP capability

        LC_019 ValidationPreparationComponent:
        Target status: included
        MVP status: partially implemented
        MVP scope: validation ready files for selected validation environment

        LC_020 TraceabilityManagementComponent:
        Target status: included
        MVP status: implemented
        MVP scope: traceability between input, intermediate results, review decisions and generated artifacts
        */
    }

    package '04_FunctionAllocation' {

        doc /*
        Function allocation to logical components:

        SF_001 IngestLegacyData:
        Allocated logical component:
        LC_003 LegacyDataIngestionComponent
        Supporting logical component:
        LC_001 UserInteractionComponent

        SF_002 ExtractInformation:
        Allocated logical component:
        LC_004 InformationExtractionComponent

        SF_003 NormalizeToCanonicalRepresentation:
        Allocated logical component:
        LC_005 CanonicalRepresentationComponent

        SF_004 CreateNormalizedInformationUnits:
        Allocated logical component:
        LC_006 InformationUnitManagementComponent
        Supporting logical component:
        LC_020 TraceabilityManagementComponent

        SF_005 AssessInformationQuality:
        Allocated logical component:
        LC_007 InformationQualityAssessmentComponent

        SF_006 SupportControlledDataCompletion:
        Allocated logical component:
        LC_008 ControlledDataCompletionComponent
        Supporting logical components:
        LC_001 UserInteractionComponent
        LC_013 HumanDecisionManagementComponent

        SF_007 GenerateCandidateResults:
        Allocated logical component:
        LC_009 CandidateGenerationComponent
        Supporting logical component:
        LC_010 AgentProfileManagementComponent

        SF_008 CompareCandidateResults:
        Allocated logical component:
        LC_011 CandidateComparisonComponent

        SF_009 GenerateReviewReport:
        Allocated logical component:
        LC_012 ReviewReportingComponent
        Supporting logical component:
        LC_020 TraceabilityManagementComponent

        SF_010 CaptureHumanDecision:
        Allocated logical component:
        LC_013 HumanDecisionManagementComponent
        Supporting logical component:
        LC_001 UserInteractionComponent

        SF_011 AlignTerminology:
        Allocated logical component:
        LC_014 TerminologyAlignmentComponent

        SF_012 DetectSemanticConflicts:
        Allocated logical component:
        LC_015 SemanticConflictDetectionComponent

        SF_013 ApplyArchitectureConstraints:
        Allocated logical component:
        LC_016 ArchitectureConstraintEvaluationComponent

        SF_014 GenerateSysMLv2Artifacts:
        Allocated logical component:
        LC_017 SysMLv2SynthesisComponent
        Supporting logical components:
        LC_016 ArchitectureConstraintEvaluationComponent
        LC_020 TraceabilityManagementComponent

        SF_015 MaintainInteractionAndInterfaceConsistency:
        Allocated logical component:
        LC_018 InteractionAndInterfaceConsistencyComponent

        SF_016 PrepareValidationWorkflow:
        Allocated logical component:
        LC_019 ValidationPreparationComponent

        SF_017 ProvideUserInteraction:
        Allocated logical component:
        LC_001 UserInteractionComponent

        SF_018 SupportExtensiblePipelineExecution:
        Allocated logical component:
        LC_002 PipelineOrchestrationComponent
        Supporting logical components:
        LC_001 UserInteractionComponent
        */
    }

    package '05_Traceability' {

        doc /*
        Logical component traceability to system requirements and design constraints:

        LC_001 UserInteractionComponent:
        SYSR_034, SYSR_035, SYSR_036, SYSR_037, SYSR_038, SYSR_039
        SYSC_014, SYSC_015

        LC_002 PipelineOrchestrationComponent:
        SYSR_029, SYSR_030, SYSR_031, SYSR_032, SYSR_033
        SYSC_001, SYSC_002, SYSC_003, SYSC_004, SYSC_011, SYSC_012

        LC_003 LegacyDataIngestionComponent:
        SYSR_001, SYSR_035

        LC_004 InformationExtractionComponent:
        SYSR_002

        LC_005 CanonicalRepresentationComponent:
        SYSR_003
        SYSC_013

        LC_006 InformationUnitManagementComponent:
        SYSR_004, SYSR_005

        LC_007 InformationQualityAssessmentComponent:
        SYSR_006

        LC_008 ControlledDataCompletionComponent:
        SYSR_007

        LC_009 CandidateGenerationComponent:
        SYSR_008, SYSR_009 

        LC_010 AgentProfileManagementComponent:
        SYSC_005, SYSC_006

        LC_011 CandidateComparisonComponent:
        SYSR_011, SYSR_012, SYSR_013
        SYSC_007

        LC_012 ReviewReportingComponent:
        SYSR_010, SYSR_014, SYSR_018
 
        LC_013 HumanDecisionManagementComponent:
        SYSR_015, SYSR_016, SYSR_017

        LC_014 TerminologyAlignmentComponent:
        SYSR_019

        LC_015 SemanticConflictDetectionComponent:
        SYSR_020

        LC_016 ArchitectureConstraintEvaluationComponent:
        SYSR_021
        SYSC_008, SYSC_009

        LC_017 SysMLv2SynthesisComponent:
        SYSR_022, SYSR_024, SYSR_025, SYSR_026

        LC_018 InteractionAndInterfaceConsistencyComponent:
        SYSR_023

        LC_019 ValidationPreparationComponent:
        SYSR_027, SYSR_028
        SYSC_010

        LC_020 TraceabilityManagementComponent:
        SYSR_004, SYSR_014, SYSR_018, SYSR_026

        Completeness check for target logical architecture:
        All system requirements SYSR_001 to SYSR_039 are covered by the target logical architecture.
        All system design constraints SYSC_001 to SYSC_015 are covered by the target logical architecture.

        Completeness check for MVP logical architecture:
        The MVP logical architecture covers the selected executable subset of the target architecture.
        Requirements marked as target or post MVP remain represented in the target logical architecture,
        but are not necessarily implemented in the MVP.
        */
    }
}