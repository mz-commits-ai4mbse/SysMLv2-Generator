package Turing_System_Requirements {

    doc /*
    Purpose:
    This package documents the system requirements of the Turing Generator.

    Modeling status:
    Transitional SysIDE shadow model.

    The stakeholder level is currently modeled in CATIA Magic SoSA. Traceability to stakeholder requirements
    is documented inside doc blocks to avoid broken cross references in SysIDE.

    Scope status definitions:

    mvp:
    Required for the first executable beta version.

    target:
    Required for the intended complete product architecture.

    post_mvp:
    Intended extension after the MVP.

    deferred:
    Known possible extension, but not required for the thesis prototype.

    Note:
    Architecture constraints are separated into the package Turing_System_DesignConstraints.
    */

    package RequirementDefinitions {

        requirement def SystemRequirement {
            doc /*
            Base type for all system requirements of the Turing Generator.
            */
        }

        requirement def DataSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to ingestion, extraction, normalization and internal data representation.
            */
        }

        requirement def FunctionalSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to system behavior and functional processing capability.
            */
        }

        requirement def AssuranceSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to human review, explanation, approval and controlled intervention.
            */
        }

        requirement def SemanticSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to vocabulary alignment, ontology based interpretation and semantic conflict detection.
            */
        }

        requirement def ArchitectureSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to modularity, structural pattern conformance and integration suitability.
            */
        }

        requirement def InterfaceSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to file interfaces, target notation compatibility and generated artifacts.
            */
        }

        requirement def ValidationSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to validation of generated results and feedback handling.
            */
        }

        requirement def UserInterfaceSystemRequirement :> SystemRequirement {
            doc /*
            Requirement related to the rudimentary user interface required for human in the loop interaction.
            */
        }
    }

    package Terminology {

        item def NormalizedInformationUnit {
            doc /*
            A normalized information unit is a bounded and source traceable portion of extracted legacy information
            that can be processed, reviewed and transformed independently.

            The term is used instead of processing unit to avoid implementation specific wording.
            */
        }

        item def CandidateResult {
            doc /*
            A candidate result is one possible output of a processing task before human review and approval.
            */
        }

        item def IntermediateResult {
            doc /*
            An intermediate result is a reviewed and approved result of a processing step that can be used as input
            for a subsequent processing step.
            */
        }

        item def SysMLv2Artifact {
            doc /*
            A generated artifact containing SysML v2 textual model content.
            */
        }
    }

    package DataProcessingRequirements {

        requirement <SYSR_001> IngestMachineReadableLegacyData : RequirementDefinitions::DataSystemRequirement {
            doc /*
            The system shall ingest machine readable legacy engineering data artifacts.

            Scope:
            mvp

            Rationale:
            Legacy data shall not be assumed to be available as JSON. JSON is used as internal canonical
            intermediate format only.

            Traceability to stakeholder requirements:
            SR_001 Input Data Suitability Assessment
            SR_006 SysML v2 Model Synthesis
            */
        }

        requirement <SYSR_002> ExtractInformationFromLegacyArtifacts : RequirementDefinitions::DataSystemRequirement {
            doc /*
            The system shall extract text, tables or structured content from ingested legacy engineering artifacts.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_001 Input Data Suitability Assessment
            SR_002 Input Data Completeness Check
            SR_003 Input Data Consistency Check
            */
        }

        requirement <SYSR_003> NormalizeToCanonicalJson : RequirementDefinitions::DataSystemRequirement {
            doc /*
            The system shall normalize extracted information into an internal JSON based canonical intermediate representation.

            Scope:
            mvp

            Rationale:
            The JSON representation separates ingestion from downstream processing and provides a stable
            interface between processing steps.

            Traceability to stakeholder requirements:
            SR_001 Input Data Suitability Assessment
            SR_006 SysML v2 Model Synthesis
            SR_019 Source Traceability
            */
        }

        requirement <SYSR_004> PreserveSourceMetadata : RequirementDefinitions::DataSystemRequirement {
            doc /*
            The system shall preserve source metadata for each extracted information unit.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_019 Source Traceability
            SR_014 Explanation of Modeling Decisions
            */
        }

        requirement <SYSR_005> SplitInformationIntoNormalizedInformationUnits : RequirementDefinitions::DataSystemRequirement {
            doc /*
            The system shall split normalized information into bounded normalized information units before agent based processing.

            Scope:
            mvp

            Rationale:
            Input data shall be portioned to keep information units small, reviewable and traceable.

            Traceability to stakeholder requirements:
            SR_001 Input Data Suitability Assessment
            SR_023 Input Constraint Violation Detection
            */
        }

        requirement <SYSR_006> AssessNormalizedInformationUnitQuality : RequirementDefinitions::DataSystemRequirement {
            doc /*
            The system shall assess each normalized information unit for completeness, consistency, machine readability,
            reliability and relevance.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_002 Input Data Completeness Check
            SR_003 Input Data Consistency Check
            SR_004 Source Reliability Classification
            SR_005 Source Relevance Classification
            SR_023 Input Constraint Violation Detection
            */
        }

        requirement <SYSR_007> SupportControlledDataCompletion : RequirementDefinitions::DataSystemRequirement {
            doc /*
            The system shall support controlled completion of incomplete legacy data using human supplied information.

            Scope:
            target

            Traceability to stakeholder requirements:
            SR_026 Legacy Data Completion
            SR_013 Human Intervention for Conflicts
            */
        }
    }

    package CandidateGenerationRequirements {

        requirement <SYSR_008> GenerateCandidateResults : RequirementDefinitions::FunctionalSystemRequirement {
            doc /*
            The system shall generate candidate results for selected processing tasks.

            Scope:
            mvp

            Rationale:
            This requirement remains solution neutral. The architectural decision to use multiple configurable
            agent profiles is documented as a system design constraint.

            Traceability to stakeholder requirements:
            SR_012 Expert Review of Generated Interpretations
            SR_015 Model Content Validation
            */
        }

        requirement <SYSR_009> SupportConfigurableCandidateGeneration : RequirementDefinitions::FunctionalSystemRequirement {
            doc /*
            The system shall support configurable candidate generation for selected processing tasks.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_012 Expert Review of Generated Interpretations
            SR_014 Explanation of Modeling Decisions
            */
        }

        requirement <SYSR_010> GenerateCandidateRationales : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall provide rationales for generated candidate results.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_011 Ambiguity Detection
            SR_012 Expert Review of Generated Interpretations
            SR_014 Explanation of Modeling Decisions
            */
        }

        requirement <SYSR_011> CompareCandidateResults : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall compare candidate results generated for the same processing task.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_011 Ambiguity Detection
            SR_012 Expert Review of Generated Interpretations
            SR_014 Explanation of Modeling Decisions
            */
        }

        requirement <SYSR_012> PresentCandidateDifferences : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall identify and present differences between candidate results.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_011 Ambiguity Detection
            SR_012 Expert Review of Generated Interpretations
            SR_014 Explanation of Modeling Decisions
            */
        }

        requirement <SYSR_013> PresentCandidateAgreement : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall indicate agreement between candidate results as part of the review information.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_012 Expert Review of Generated Interpretations
            SR_015 Model Content Validation
            */
        }
    }

    package HumanReviewRequirements {

        requirement <SYSR_014> GenerateReviewReport : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall generate review reports that present candidate results, identified differences,
            rationales, source references and required human decisions.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_012 Expert Review of Generated Interpretations
            SR_014 Explanation of Modeling Decisions
            SR_019 Source Traceability
            */
        }

        requirement <SYSR_015> RequireHumanApproval : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall require human approval before an intermediate result is used as input for a subsequent processing step.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_013 Human Intervention for Conflicts
            SR_015 Model Content Validation
            */
        }

        requirement <SYSR_016> ProvideHumanDecisionOptions : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall provide human decision options for accepting, rejecting or modifying intermediate results.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_013 Human Intervention for Conflicts
            SR_015 Model Content Validation
            SR_026 Legacy Data Completion
            */
        }

        requirement <SYSR_017> RecordHumanDecision : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall record the human decision together with the reviewed candidate result.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_013 Human Intervention for Conflicts
            SR_015 Model Content Validation
            SR_019 Source Traceability
            */
        }

        requirement <SYSR_018> ExplainModelingDecisions : RequirementDefinitions::AssuranceSystemRequirement {
            doc /*
            The system shall provide rationales for generated candidate results and generated SysML v2 model elements.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_014 Explanation of Modeling Decisions
            SR_019 Source Traceability
            */
        }
    }

    package SemanticAndArchitectureRequirements {

        requirement <SYSR_019> AlignTermsWithVocabulary : RequirementDefinitions::SemanticSystemRequirement {
            doc /*
            The system shall align extracted terms with a defined technical vocabulary before model synthesis.

            Scope:
            target

            Traceability to stakeholder requirements:
            SR_016 Technical Vocabulary Alignment
            SR_017 Semantic Equivalence Handling
            */
        }

        requirement <SYSR_020> DetectSemanticConflicts : RequirementDefinitions::SemanticSystemRequirement {
            doc /*
            The system shall identify ontology or vocabulary conflicts in candidate results.

            Scope:
            target

            Traceability to stakeholder requirements:
            SR_018 Ontology Conflict Detection
            */
        }

        requirement <SYSR_021> ApplyArchitectureConstraints : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall apply defined architectural constraints during model synthesis.

            Scope:
            target

            Traceability to stakeholder requirements:
            SR_022 Architectural Constraint Conformance
            SR_025 Reusable Architectural Pattern Application
            */
        }

        requirement <SYSR_022> GenerateModularTargetModelStructures : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall generate modular SysML v2 structures that can be integrated into a defined target model structure.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_008 Model Reusability
            SR_009 Modular Model Growth
            SR_010 Non Destructive Submodel Integration
            SR_021 Larger Context Compatibility
            */
        }

        requirement <SYSR_023> MaintainGeneratedInteractionAndInterfaceConsistency : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall maintain consistency of generated interaction and interface related model elements.

            Scope:
            post_mvp

            Rationale:
            This requirement addresses consistency of generated interaction and interface structures, such as ports,
            item flows, dependencies or other interface related model elements, depending on the selected SysML v2
            target notation subset.

            Traceability to stakeholder requirements:
            SR_024 Interface Definition Consistency
            */
        }
    }

    package SysMLv2SynthesisAndValidationRequirements {

        requirement <SYSR_024> GenerateSysMLv2TargetNotation : RequirementDefinitions::InterfaceSystemRequirement {
            doc /*
            The system shall generate SysML v2 text output according to a defined SysML v2 target notation.

            Scope:
            mvp

            Rationale:
            The MVP shall cut scope by limiting the generated SysML v2 language subset, not by accepting invalid syntax.

            Traceability to stakeholder requirements:
            SR_006 SysML v2 Model Synthesis
            SR_007 Structural Pattern Conformance
            */
        }

        requirement <SYSR_025> GenerateTargetProjectStructure : RequirementDefinitions::InterfaceSystemRequirement {
            doc /*
            The system shall generate output files according to a defined target project structure.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_007 Structural Pattern Conformance
            SR_010 Non Destructive Submodel Integration
            SR_025 Reusable Architectural Pattern Application
            */
        }

        requirement <SYSR_026> PreserveTraceabilityInGeneratedModel : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall preserve traceability between generated SysML v2 elements and their originating source information.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_019 Source Traceability
            SR_014 Explanation of Modeling Decisions
            */
        }

        requirement <SYSR_027> SupportValidationWorkflow : RequirementDefinitions::ValidationSystemRequirement {
            doc /*
            The system shall provide generated SysML v2 files in a structure that supports validation by the selected validation environment.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_015 Model Content Validation
            SR_020 Integrated Model Consistency
            SR_024 Interface Definition Consistency
            */
        }

        requirement <SYSR_028> ReportValidationFindings : RequirementDefinitions::ValidationSystemRequirement {
            doc /*
            The system shall report syntactic and structural validation findings to the user.

            Scope:
            post_mvp

            Traceability to stakeholder requirements:
            SR_014 Explanation of Modeling Decisions
            SR_015 Model Content Validation
            SR_020 Integrated Model Consistency
            */
        }
    }

    package ExtensibilityRequirements {

        requirement <SYSR_029> ProvideExtensibleProcessingStructure : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall provide an extensible processing structure.

            Scope:
            mvp

            Rationale:
            The MVP shall be extendable into a later complete product without redesigning the processing core.

            Traceability to stakeholder requirements:
            SR_008 Model Reusability
            SR_009 Modular Model Growth
            SR_010 Non Destructive Submodel Integration
            SR_021 Larger Context Compatibility
            */
        }

        requirement <SYSR_030> SeparateControlFlowFromProcessingCapabilities : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall separate control flow from task specific processing capabilities.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_009 Modular Model Growth
            SR_010 Non Destructive Submodel Integration
            */
        }

        requirement <SYSR_031> AssignDistinctProcessingResponsibilities : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall assign distinct processing responsibilities to distinct processing capabilities.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_008 Model Reusability
            SR_009 Modular Model Growth
            */
        }

        requirement <SYSR_032> SupportExtensionThroughDefinedModuleInterfaces : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall support extension through additional processing modules that conform to defined module interfaces.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_008 Model Reusability
            SR_009 Modular Model Growth
            SR_010 Non Destructive Submodel Integration
            */
        }

        requirement <SYSR_033> SupportConfigurablePipelineExecution : RequirementDefinitions::ArchitectureSystemRequirement {
            doc /*
            The system shall support configurable execution of selected pipeline capabilities.

            Scope:
            mvp

            Rationale:
            This system requirement will later be allocated to the orchestration function or orchestration component.

            Traceability to stakeholder requirements:
            SR_009 Modular Model Growth
            SR_021 Larger Context Compatibility
            */
        }
    }

    package UserInterfaceRequirements {

        requirement <SYSR_034> ProvideRudimentaryUserInterface : RequirementDefinitions::UserInterfaceSystemRequirement {
            doc /*
            The system shall provide a rudimentary user interface for starting and monitoring a processing run.

            Scope:
            mvp

            Rationale:
            The user interface provides the interaction point for the human in the loop workflow.

            Traceability to stakeholder requirements:
            SR_012 Expert Review of Generated Interpretations
            SR_013 Human Intervention for Conflicts
            */
        }

        requirement <SYSR_035> SupportFileUploadInUserInterface : RequirementDefinitions::UserInterfaceSystemRequirement {
            doc /*
            The system shall allow the user to provide machine readable legacy engineering data through the user interface.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_001 Input Data Suitability Assessment
            SR_006 SysML v2 Model Synthesis
            */
        }

        requirement <SYSR_036> PresentIngestionPreview : RequirementDefinitions::UserInterfaceSystemRequirement {
            doc /*
            The system shall present extracted and normalized information before agent based processing continues.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_014 Explanation of Modeling Decisions
            SR_019 Source Traceability
            */
        }

        requirement <SYSR_037> PresentReviewReportsInUserInterface : RequirementDefinitions::UserInterfaceSystemRequirement {
            doc /*
            The system shall present review reports including candidate results, identified differences, rationales and source references.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_012 Expert Review of Generated Interpretations
            SR_014 Explanation of Modeling Decisions
            SR_019 Source Traceability
            */
        }

        requirement <SYSR_038> CaptureHumanReviewDecision : RequirementDefinitions::UserInterfaceSystemRequirement {
            doc /*
            The system shall allow the user to accept, reject or modify intermediate results through the user interface.

            Scope:
            mvp

            Traceability to stakeholder requirements:
            SR_013 Human Intervention for Conflicts
            SR_015 Model Content Validation
            */
        }

        requirement <SYSR_039> ProvideAccessToGeneratedSysMLv2Artifacts : RequirementDefinitions::UserInterfaceSystemRequirement {
            doc /*
            The system shall provide access to generated SysML v2 artifacts through the user interface.

            Scope:
            mvp

            Rationale:
            The generated model does not need to be rendered completely in the user interface. The user interface
            shall at least provide access to generated artifacts for review, download or further validation.

            Traceability to stakeholder requirements:
            SR_006 SysML v2 Model Synthesis
            SR_014 Explanation of Modeling Decisions
            */
        }
    }
}