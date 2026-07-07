package Turing_System_Physical {

    doc /*
    Purpose:
    This package documents the physical MVP architecture of the Turing Generator.

    Modeling status:
    Transitional SysIDE shadow model.

    Scope:
    This physical perspective describes the MVP realization only.
    The complete target product is intentionally not physically modeled at this stage.

    Modeling decision:
    The MVP physical architecture realizes a selected subset of the logical target architecture.
    Physical MVP elements are implementation oriented, but still remain above concrete source code level.

    Relation to implementation:
    This package prepares the transition from logical architecture to Python implementation.
    Concrete Python files, classes and functions will be derived from this MVP physical architecture.
    */

    package '00_PhysicalDefinitions' {

        part def PhysicalElement {
            doc /*
            Base type for physical MVP architecture elements.
            */
        }

        part def PhysicalComponent :> PhysicalElement {
            doc /*
            Physical component used to realize one or more logical components in the MVP.
            */
        }

        part def PhysicalConfiguration :> PhysicalElement {
            doc /*
            Configuration artifact used by the MVP physical architecture.
            */
        }

        part def PhysicalDataStore :> PhysicalElement {
            doc /*
            Physical data store or workspace used by the MVP.
            */
        }

        part def PhysicalArtifact :> PhysicalElement {
            doc /*
            Physical artifact produced, consumed or exchanged by the MVP implementation.
            */
        }

        part def UIApplication :> PhysicalComponent {
            doc /*
            Physical MVP component providing the user facing application.

            Expected implementation role:
            Provides file upload, ingestion preview, review report display, human decision capture
            and access to generated SysML v2 artifacts.

            Later Python realization candidate:
            app/ui_app.py
            */
        }

        part def MVPOrchestrator :> PhysicalComponent {
            doc /*
            Physical MVP component coordinating the selected processing pipeline.

            Expected implementation role:
            Calls processing modules, manages execution order, transfers intermediate data,
            handles execution state and reports status or errors to the user interface.

            Later Python realization candidate:
            core/orchestrator.py
            */
        }

        part def PipelineConfiguration :> PhysicalConfiguration {
            doc /*
            Physical configuration artifact defining which processing steps are active in the MVP.

            Expected implementation role:
            Defines selected MVP pipeline capabilities and their execution order.

            Later Python realization candidate:
            core/pipeline_config.py or config/pipeline_config.json
            */
        }

        part def FileIngestionAdapter :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for accepting selected machine readable legacy files.

            Expected implementation role:
            Receives uploaded files, stores them in the workspace and prepares them for extraction.

            Later Python realization candidate:
            modules/ingestion/file_ingestion_adapter.py
            */
        }

        part def TextExtractionAdapter :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for extracting text, tables or structured content
            from selected machine readable input files.

            Later Python realization candidate:
            modules/extraction/text_extraction_adapter.py
            */
        }

        part def CanonicalJsonBuilder :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for creating the internal JSON based canonical representation.

            Later Python realization candidate:
            modules/normalization/canonical_json_builder.py
            */
        }

        part def InformationUnitBuilder :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for creating bounded and source traceable normalized information units.

            Later Python realization candidate:
            modules/normalization/information_unit_builder.py
            */
        }

        part def BasicQualityAssessmentService :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for basic assessment of completeness, consistency,
            machine readability, relevance and reliability.

            Later Python realization candidate:
            modules/quality/basic_quality_assessment.py
            */
        }

        part def AgentProfileConfiguration :> PhysicalConfiguration {
            doc /*
            Physical configuration artifact defining the limited configurable agent profiles used in the MVP.

            Later Python realization candidate:
            modules/agents/agent_profile_config.py or config/agent_profiles.json
            */
        }

        part def CandidateGenerationRunner :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for executing candidate generation for selected processing tasks.

            Later Python realization candidate:
            modules/agents/candidate_generation_runner.py
            */
        }

        part def CandidateComparisonService :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for comparing candidate results and identifying differences
            and agreement as review information.

            Later Python realization candidate:
            modules/review/candidate_comparison_service.py
            */
        }

        part def ReviewReportGenerator :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for generating review reports from candidate results,
            rationales, comparisons and source references.

            Later Python realization candidate:
            modules/review/review_report_generator.py
            */
        }

        part def HumanDecisionStore :> PhysicalDataStore {
            doc /*
            Physical MVP element responsible for storing human accept, reject or modify decisions.

            Later Python realization candidate:
            modules/review/human_decision_store.py or data/intermediate/decisions
            */
        }

        part def SysMLv2ArtifactWriter :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for generating textual SysML v2 artifacts according to
            the selected target notation subset and project structure.

            Later Python realization candidate:
            modules/synthesis/sysml_artifact_writer.py
            */
        }

        part def ValidationPreparationAdapter :> PhysicalComponent {
            doc /*
            Physical MVP component responsible for preparing generated SysML v2 files for validation
            in the selected validation environment.

            Later Python realization candidate:
            modules/validation/validation_preparation_adapter.py
            */
        }

        part def TraceabilityStore :> PhysicalDataStore {
            doc /*
            Physical MVP element responsible for storing traceability links between input artifacts,
            extracted content, normalized information units, candidate results, review decisions and generated artifacts.

            Later Python realization candidate:
            modules/traceability/traceability_store.py or data/intermediate/traceability
            */
        }

        part def FileSystemWorkspace :> PhysicalDataStore {
            doc /*
            Physical MVP workspace used to store input files, intermediate representations, reports,
            decisions, generated artifacts and validation ready files.

            Later physical folder candidate:
            data/
            */
        }

        item def UploadedLegacyFile {
            doc /*
            Physical file uploaded or provided to the MVP as machine readable legacy engineering data.
            */
        }

        item def ExtractedContentFile {
            doc /*
            Physical artifact containing extracted content from uploaded legacy files.
            */
        }

        item def CanonicalJsonFile {
            doc /*
            Physical JSON artifact containing the canonical intermediate representation.
            */
        }

        item def InformationUnitFile {
            doc /*
            Physical artifact containing bounded normalized information units.
            */
        }

        item def QualityAssessmentFile {
            doc /*
            Physical artifact containing basic quality assessment results.
            */
        }

        item def CandidateResultFile {
            doc /*
            Physical artifact containing generated candidate results and rationales.
            */
        }

        item def CandidateComparisonFile {
            doc /*
            Physical artifact containing candidate differences and agreement information.
            */
        }

        item def ReviewReportFile {
            doc /*
            Physical artifact containing the review report presented to the human user.
            */
        }

        item def HumanDecisionFile {
            doc /*
            Physical artifact containing the recorded human decision.
            */
        }

        item def GeneratedSysMLv2File {
            doc /*
            Physical artifact containing generated textual SysML v2 content.
            */
        }

        item def ValidationReadyProject {
            doc /*
            Physical artifact or folder structure prepared for validation by the selected validation environment.
            */
        }
    }

    package '01_MVPPhysicalArchitecture' {

        part def MVPPhysicalArchitecture {
            doc /*
            Physical architecture of the MVP.

            The MVP physical architecture realizes only the executable subset of the logical architecture.
            Target only and post MVP capabilities are not physically realized here.

            Main architectural principle:
            The MVP is implemented as a modular pipeline coordinated by an orchestrator.
            Individual physical components provide distinct processing capabilities.
            */

            part uiApplication : '00_PhysicalDefinitions'::UIApplication;
            part mvpOrchestrator : '00_PhysicalDefinitions'::MVPOrchestrator;
            part pipelineConfiguration : '00_PhysicalDefinitions'::PipelineConfiguration;
            part fileIngestionAdapter : '00_PhysicalDefinitions'::FileIngestionAdapter;
            part textExtractionAdapter : '00_PhysicalDefinitions'::TextExtractionAdapter;
            part canonicalJsonBuilder : '00_PhysicalDefinitions'::CanonicalJsonBuilder;
            part informationUnitBuilder : '00_PhysicalDefinitions'::InformationUnitBuilder;
            part basicQualityAssessmentService : '00_PhysicalDefinitions'::BasicQualityAssessmentService;
            part agentProfileConfiguration : '00_PhysicalDefinitions'::AgentProfileConfiguration;
            part candidateGenerationRunner : '00_PhysicalDefinitions'::CandidateGenerationRunner;
            part candidateComparisonService : '00_PhysicalDefinitions'::CandidateComparisonService;
            part reviewReportGenerator : '00_PhysicalDefinitions'::ReviewReportGenerator;
            part humanDecisionStore : '00_PhysicalDefinitions'::HumanDecisionStore;
            part sysMLv2ArtifactWriter : '00_PhysicalDefinitions'::SysMLv2ArtifactWriter;
            part validationPreparationAdapter : '00_PhysicalDefinitions'::ValidationPreparationAdapter;
            part traceabilityStore : '00_PhysicalDefinitions'::TraceabilityStore;
            part fileSystemWorkspace : '00_PhysicalDefinitions'::FileSystemWorkspace;
        }

        part mvpPhysicalArchitecture : MVPPhysicalArchitecture;
    }

    package '02_MVPModuleStructure' {

        doc /*
        Planned MVP module structure:

        app/
            ui_app.py
            Purpose:
            User facing MVP application for upload, preview, review, decision capture and artifact access.

        core/
            orchestrator.py
            Purpose:
            Central execution coordinator for the MVP pipeline.

            pipeline_config.py
            Purpose:
            Defines selected processing steps and execution configuration.

            run_context.py
            Purpose:
            Holds run state, paths, status information and execution metadata.

        modules/ingestion/
            file_ingestion_adapter.py
            Purpose:
            Receives selected machine readable legacy files and registers them in the workspace.

        modules/extraction/
            text_extraction_adapter.py
            Purpose:
            Extracts text, tables or structured content from selected input files.

        modules/normalization/
            canonical_json_builder.py
            Purpose:
            Builds the internal JSON based canonical intermediate representation.

            information_unit_builder.py
            Purpose:
            Creates bounded and source traceable normalized information units.

        modules/quality/
            basic_quality_assessment.py
            Purpose:
            Performs basic quality assessment on normalized information units.

        modules/agents/
            agent_profile_config.py
            Purpose:
            Defines limited configurable agent profiles for the MVP.

            candidate_generation_runner.py
            Purpose:
            Executes candidate generation for selected processing tasks.

        modules/review/
            candidate_comparison_service.py
            Purpose:
            Compares candidate results and identifies differences and agreement.

            review_report_generator.py
            Purpose:
            Generates human review reports.

            human_decision_store.py
            Purpose:
            Stores accept, reject or modify decisions.

        modules/synthesis/
            sysml_artifact_writer.py
            Purpose:
            Writes generated SysML v2 textual artifacts.

        modules/validation/
            validation_preparation_adapter.py
            Purpose:
            Prepares generated files for validation.

        modules/traceability/
            traceability_store.py
            Purpose:
            Stores traceability between input, intermediate results, review decisions and generated artifacts.

        data/
            input/
            extracted/
            intermediate/
            reports/
            decisions/
            output/
            validation/
            traceability/
        */
    }

    package '03_LogicalToPhysicalMapping' {

        doc /*
        Logical to physical MVP mapping:

        LC_001 UserInteractionComponent:
        Physical realization:
        PC_001 UIApplication
        MVP status:
        partially implemented
        MVP scope:
        file upload, ingestion preview, review report display, human decision capture, artifact access

        LC_002 PipelineOrchestrationComponent:
        Physical realization:
        PC_002 MVPOrchestrator
        PC_003 PipelineConfiguration
        MVP status:
        implemented
        MVP scope:
        selected pipeline execution, data handover, status and error reporting

        LC_003 LegacyDataIngestionComponent:
        Physical realization:
        PC_004 FileIngestionAdapter
        PC_017 FileSystemWorkspace
        MVP status:
        implemented

        LC_004 InformationExtractionComponent:
        Physical realization:
        PC_005 TextExtractionAdapter
        MVP status:
        implemented

        LC_005 CanonicalRepresentationComponent:
        Physical realization:
        PC_006 CanonicalJsonBuilder
        MVP status:
        implemented

        LC_006 InformationUnitManagementComponent:
        Physical realization:
        PC_007 InformationUnitBuilder
        PC_016 TraceabilityStore
        MVP status:
        implemented

        LC_007 InformationQualityAssessmentComponent:
        Physical realization:
        PC_008 BasicQualityAssessmentService
        MVP status:
        partially implemented
        MVP scope:
        basic quality criteria only

        LC_008 ControlledDataCompletionComponent:
        Physical realization:
        none in MVP
        MVP status:
        not implemented
        Reason:
        target capability, not required for first executable MVP

        LC_009 CandidateGenerationComponent:
        Physical realization:
        PC_010 CandidateGenerationRunner
        MVP status:
        implemented

        LC_010 AgentProfileManagementComponent:
        Physical realization:
        PC_009 AgentProfileConfiguration
        PC_010 CandidateGenerationRunner
        MVP status:
        partially implemented
        MVP scope:
        limited configurable agent profiles

        LC_011 CandidateComparisonComponent:
        Physical realization:
        PC_011 CandidateComparisonService
        MVP status:
        implemented

        LC_012 ReviewReportingComponent:
        Physical realization:
        PC_012 ReviewReportGenerator
        MVP status:
        implemented

        LC_013 HumanDecisionManagementComponent:
        Physical realization:
        PC_013 HumanDecisionStore
        PC_001 UIApplication
        MVP status:
        implemented

        LC_014 TerminologyAlignmentComponent:
        Physical realization:
        none in MVP
        MVP status:
        not implemented or stubbed
        Reason:
        target capability, may be added after MVP

        LC_015 SemanticConflictDetectionComponent:
        Physical realization:
        none in MVP
        MVP status:
        not implemented or stubbed
        Reason:
        target capability, may be added after MVP

        LC_016 ArchitectureConstraintEvaluationComponent:
        Physical realization:
        PC_014 SysMLv2ArtifactWriter
        PC_015 ValidationPreparationAdapter
        MVP status:
        partially implemented
        MVP scope:
        limited target notation and project structure constraints

        LC_017 SysMLv2SynthesisComponent:
        Physical realization:
        PC_014 SysMLv2ArtifactWriter
        MVP status:
        implemented

        LC_018 InteractionAndInterfaceConsistencyComponent:
        Physical realization:
        none in MVP
        MVP status:
        not implemented
        Reason:
        post MVP capability

        LC_019 ValidationPreparationComponent:
        Physical realization:
        PC_015 ValidationPreparationAdapter
        MVP status:
        partially implemented
        MVP scope:
        validation ready files for selected validation environment

        LC_020 TraceabilityManagementComponent:
        Physical realization:
        PC_016 TraceabilityStore
        PC_017 FileSystemWorkspace
        MVP status:
        implemented
        */
    }

    package '04_MVPDataAndArtifactFlow' {

        doc /*
        MVP data and artifact flow:

        1. Uploaded legacy file
        Source:
        UIApplication
        Target:
        FileIngestionAdapter
        Stored artifact:
        UploadedLegacyFile in data/input/

        2. Extracted content
        Source:
        TextExtractionAdapter
        Target:
        CanonicalJsonBuilder
        Stored artifact:
        ExtractedContentFile in data/extracted/

        3. Canonical intermediate representation
        Source:
        CanonicalJsonBuilder
        Target:
        InformationUnitBuilder
        Stored artifact:
        CanonicalJsonFile in data/intermediate/

        4. Normalized information units
        Source:
        InformationUnitBuilder
        Target:
        BasicQualityAssessmentService
        Stored artifact:
        InformationUnitFile in data/intermediate/

        5. Quality assessment
        Source:
        BasicQualityAssessmentService
        Target:
        CandidateGenerationRunner
        Stored artifact:
        QualityAssessmentFile in data/intermediate/

        6. Candidate results
        Source:
        CandidateGenerationRunner
        Target:
        CandidateComparisonService
        Stored artifact:
        CandidateResultFile in data/intermediate/

        7. Candidate comparison
        Source:
        CandidateComparisonService
        Target:
        ReviewReportGenerator
        Stored artifact:
        CandidateComparisonFile in data/intermediate/

        8. Review report
        Source:
        ReviewReportGenerator
        Target:
        UIApplication
        Stored artifact:
        ReviewReportFile in data/reports/

        9. Human decision
        Source:
        UIApplication
        Target:
        HumanDecisionStore
        Stored artifact:
        HumanDecisionFile in data/decisions/

        10. Generated SysML v2 artifact
        Source:
        SysMLv2ArtifactWriter
        Target:
        ValidationPreparationAdapter and UIApplication
        Stored artifact:
        GeneratedSysMLv2File in data/output/

        11. Validation ready project
        Source:
        ValidationPreparationAdapter
        Target:
        Selected validation environment
        Stored artifact:
        ValidationReadyProject in data/validation/

        12. Traceability records
        Source:
        All processing steps
        Target:
        TraceabilityStore
        Stored artifact:
        Traceability data in data/traceability/
        */
    }

    package '05_FunctionToPhysicalAllocation' {

        doc /*
        System function to physical MVP element allocation:

        SF_001 IngestLegacyData:
        Primary physical element:
        PC_004 FileIngestionAdapter
        Supporting physical elements:
        PC_001 UIApplication
        PC_017 FileSystemWorkspace

        SF_002 ExtractInformation:
        Primary physical element:
        PC_005 TextExtractionAdapter

        SF_003 NormalizeToCanonicalRepresentation:
        Primary physical element:
        PC_006 CanonicalJsonBuilder

        SF_004 CreateNormalizedInformationUnits:
        Primary physical element:
        PC_007 InformationUnitBuilder
        Supporting physical element:
        PC_016 TraceabilityStore

        SF_005 AssessInformationQuality:
        Primary physical element:
        PC_008 BasicQualityAssessmentService

        SF_006 SupportControlledDataCompletion:
        Primary physical element:
        Not physically realized in MVP

        SF_007 GenerateCandidateResults:
        Primary physical element:
        PC_010 CandidateGenerationRunner
        Supporting physical element:
        PC_009 AgentProfileConfiguration

        SF_008 CompareCandidateResults:
        Primary physical element:
        PC_011 CandidateComparisonService

        SF_009 GenerateReviewReport:
        Primary physical element:
        PC_012 ReviewReportGenerator
        Supporting physical element:
        PC_016 TraceabilityStore

        SF_010 CaptureHumanDecision:
        Primary physical element:
        PC_013 HumanDecisionStore
        Supporting physical element:
        PC_001 UIApplication

        SF_011 AlignTerminology:
        Primary physical element:
        Not physically realized in MVP

        SF_012 DetectSemanticConflicts:
        Primary physical element:
        Not physically realized in MVP

        SF_013 ApplyArchitectureConstraints:
        Primary physical element:
        PC_014 SysMLv2ArtifactWriter
        Supporting physical element:
        PC_015 ValidationPreparationAdapter
        MVP note:
        Implemented only as limited target notation and project structure constraints.

        SF_014 GenerateSysMLv2Artifacts:
        Primary physical element:
        PC_014 SysMLv2ArtifactWriter
        Supporting physical element:
        PC_016 TraceabilityStore

        SF_015 MaintainInteractionAndInterfaceConsistency:
        Primary physical element:
        Not physically realized in MVP

        SF_016 PrepareValidationWorkflow:
        Primary physical element:
        PC_015 ValidationPreparationAdapter

        SF_017 ProvideUserInteraction:
        Primary physical element:
        PC_001 UIApplication

        SF_018 SupportExtensiblePipelineExecution:
        Primary physical element:
        PC_002 MVPOrchestrator
        Supporting physical elements:
        PC_003 PipelineConfiguration
        PC_001 UIApplication
        */
    }

    package '06_Traceability' {

        doc /*
        Physical MVP traceability to logical components:

        PC_001 UIApplication:
        Realizes:
        LC_001 UserInteractionComponent
        Supports:
        LC_013 HumanDecisionManagementComponent
        LC_002 PipelineOrchestrationComponent

        PC_002 MVPOrchestrator:
        Realizes:
        LC_002 PipelineOrchestrationComponent

        PC_003 PipelineConfiguration:
        Supports:
        LC_002 PipelineOrchestrationComponent

        PC_004 FileIngestionAdapter:
        Realizes:
        LC_003 LegacyDataIngestionComponent

        PC_005 TextExtractionAdapter:
        Realizes:
        LC_004 InformationExtractionComponent

        PC_006 CanonicalJsonBuilder:
        Realizes:
        LC_005 CanonicalRepresentationComponent

        PC_007 InformationUnitBuilder:
        Realizes:
        LC_006 InformationUnitManagementComponent

        PC_008 BasicQualityAssessmentService:
        Realizes:
        LC_007 InformationQualityAssessmentComponent

        PC_009 AgentProfileConfiguration:
        Supports:
        LC_010 AgentProfileManagementComponent

        PC_010 CandidateGenerationRunner:
        Realizes:
        LC_009 CandidateGenerationComponent
        Supports:
        LC_010 AgentProfileManagementComponent

        PC_011 CandidateComparisonService:
        Realizes:
        LC_011 CandidateComparisonComponent

        PC_012 ReviewReportGenerator:
        Realizes:
        LC_012 ReviewReportingComponent

        PC_013 HumanDecisionStore:
        Realizes:
        LC_013 HumanDecisionManagementComponent

        PC_014 SysMLv2ArtifactWriter:
        Realizes:
        LC_017 SysMLv2SynthesisComponent
        Supports:
        LC_016 ArchitectureConstraintEvaluationComponent

        PC_015 ValidationPreparationAdapter:
        Realizes:
        LC_019 ValidationPreparationComponent
        Supports:
        LC_016 ArchitectureConstraintEvaluationComponent

        PC_016 TraceabilityStore:
        Realizes:
        LC_020 TraceabilityManagementComponent

        PC_017 FileSystemWorkspace:
        Supports:
        LC_003 LegacyDataIngestionComponent
        LC_020 TraceabilityManagementComponent

        Logical components not physically realized in MVP:
        LC_008 ControlledDataCompletionComponent
        LC_014 TerminologyAlignmentComponent
        LC_015 SemanticConflictDetectionComponent
        LC_018 InteractionAndInterfaceConsistencyComponent

        Completeness check:
        All MVP relevant logical components are physically realized by MVP physical elements.
        Target only and post MVP logical components are intentionally not physically realized in this MVP perspective.
        */
    }
}