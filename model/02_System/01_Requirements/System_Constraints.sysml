package Turing_System_DesignConstraints {

    doc /*
    Purpose:
    This package documents design constraints for the Turing Generator.

    Modeling status:
    Transitional SysIDE shadow model.

    Design constraints are separated from system requirements to keep the distinction between problem space
    and solution space explicit.

    A system requirement describes what the system shall provide.
    A system design constraint documents an intentionally selected architectural boundary condition.
    */

    package ConstraintDefinitions {

        requirement def SystemDesignConstraint {
            doc /*
            Base type for system design constraints of the Turing Generator.
            */
        }

        requirement def ArchitectureConstraint :> SystemDesignConstraint {
            doc /*
            Constraint related to the structural architecture of the Turing Generator.
            */
        }

        requirement def AgentConstraint :> SystemDesignConstraint {
            doc /*
            Constraint related to agent based candidate generation.
            */
        }

        requirement def InterfaceConstraint :> SystemDesignConstraint {
            doc /*
            Constraint related to external interfaces, target notations and validation environments.
            */
        }

        requirement def ImplementationConstraint :> SystemDesignConstraint {
            doc /*
            Constraint related to implementation structure of the MVP and later product extension.
            */
        }

        requirement def UserInterfaceConstraint :> SystemDesignConstraint {
            doc /*
            Constraint related to the user interface and its interaction with the processing system.
            */
        }
    }

    package ArchitectureDesignConstraints {

        requirement <SYSC_001> ModularPipelineArchitecture : ConstraintDefinitions::ArchitectureConstraint {
            doc /*
            The architecture shall be structured as a modular processing pipeline.

            Rationale:
            The MVP shall be a subset of the later target architecture and shall remain extendable.

            Related system requirements:
            SYSR_029 ProvideExtensibleProcessingStructure
            SYSR_030 SeparateControlFlowFromProcessingCapabilities
            SYSR_031 AssignDistinctProcessingResponsibilities
            SYSR_032 SupportExtensionThroughDefinedModuleInterfaces
            SYSR_033 SupportConfigurablePipelineExecution
            */
        }

        requirement <SYSC_002> CentralOrchestration : ConstraintDefinitions::ArchitectureConstraint {
            doc /*
            The architecture shall use a central orchestration element to coordinate pipeline execution.

            Rationale:
            Processing modules shall focus on task specific responsibilities while the orchestration element
            manages execution order, data handover and run state.

            Related system requirements:
            SYSR_030 SeparateControlFlowFromProcessingCapabilities
            SYSR_033 SupportConfigurablePipelineExecution
            */
        }

        requirement <SYSC_003> DefinedModuleInterfaces : ConstraintDefinitions::ArchitectureConstraint {
            doc /*
            Processing modules shall expose defined interfaces for inputs, outputs, execution status and error information.

            Rationale:
            Defined module interfaces support later extension by additional modules and reduce coupling between
            processing capabilities.

            Related system requirements:
            SYSR_032 SupportExtensionThroughDefinedModuleInterfaces
            */
        }

        requirement <SYSC_004> MVPAsTargetArchitectureSubset : ConstraintDefinitions::ArchitectureConstraint {
            doc /*
            The MVP shall be implemented as a selected subset of the intended target architecture.

            Rationale:
            The MVP shall not be a throwaway prototype. It shall provide a first executable and extendable
            baseline for later product expansion.

            Related system requirements:
            SYSR_029 ProvideExtensibleProcessingStructure
            SYSR_033 SupportConfigurablePipelineExecution
            */
        }
    }

    package AgentDesignConstraints {

        requirement <SYSC_005> MultipleConfigurableAgentProfiles : ConstraintDefinitions::AgentConstraint {
            doc /*
            Selected processing tasks shall support multiple configurable agent profiles.

            Rationale:
            Candidate generation can be performed from different controlled perspectives. Agreement between
            candidate results can be shown as review information, while differences can indicate review relevant
            interpretation uncertainty.

            Related system requirements:
            SYSR_008 GenerateCandidateResults
            SYSR_009 SupportConfigurableCandidateGeneration
            SYSR_011 CompareCandidateResults
            SYSR_012 PresentCandidateDifferences
            SYSR_013 PresentCandidateAgreement
            */
        }

        requirement <SYSC_006> ScalableAgentProfileCount : ConstraintDefinitions::AgentConstraint {
            doc /*
            The number of agent profiles used for a selected processing task shall be configurable.

            Rationale:
            The MVP may use a small number of profiles, while later versions may increase the number of profiles
            or specialize profiles for additional tasks.

            Related system requirements:
            SYSR_009 SupportConfigurableCandidateGeneration
            */
        }

        requirement <SYSC_007> HumanApprovalIndependentOfCandidateAgreement : ConstraintDefinitions::AgentConstraint {
            doc /*
            Human approval shall be required regardless of agreement or difference between candidate results.

            Rationale:
            Candidate agreement is review information and shall not replace the human in the loop approval decision.

            Related system requirements:
            SYSR_013 PresentCandidateAgreement
            SYSR_015 RequireHumanApproval
            SYSR_016 ProvideHumanDecisionOptions
            */
        }
    }

    package InterfaceAndNotationConstraints {

        requirement <SYSC_008> DefinedSysMLv2TargetNotation : ConstraintDefinitions::InterfaceConstraint {
            doc /*
            Generated SysML v2 output shall use a defined target notation.

            Rationale:
            The MVP shall limit the generated SysML v2 language subset, but all generated output within this
            subset shall be syntactically valid for the selected toolchain.

            Related system requirements:
            SYSR_024 GenerateSysMLv2TargetNotation
            SYSR_025 GenerateTargetProjectStructure
            SYSR_027 SupportValidationWorkflow
            */
        }

        requirement <SYSC_009> DefinedTargetProjectStructure : ConstraintDefinitions::InterfaceConstraint {
            doc /*
            Generated files shall follow a defined target project structure.

            Rationale:
            The target project structure provides a stable output contract for the generator and supports validation
            and later integration of generated model artifacts.

            Related system requirements:
            SYSR_025 GenerateTargetProjectStructure
            SYSR_027 SupportValidationWorkflow
            */
        }

        requirement <SYSC_010> ToolchainValidationCompatibility : ConstraintDefinitions::InterfaceConstraint {
            doc /*
            Generated artifacts shall be compatible with the selected validation toolchain.

            Rationale:
            Tool specific behavior shall not be hidden inside individual processing modules. Compatibility with the
            selected validation environment shall be handled through the defined target notation and project structure.

            Related system requirements:
            SYSR_024 GenerateSysMLv2TargetNotation
            SYSR_027 SupportValidationWorkflow
            SYSR_028 ReportValidationFindings
            */
        }
    }

    package ImplementationDesignConstraints {

        requirement <SYSC_011> PythonModuleBasedImplementation : ConstraintDefinitions::ImplementationConstraint {
            doc /*
            The MVP implementation shall use separate Python modules for distinct processing responsibilities.

            Rationale:
            This implementation constraint supports rapid development while preserving the modular architecture
            needed for later extension.

            Related system requirements:
            SYSR_031 AssignDistinctProcessingResponsibilities
            SYSR_032 SupportExtensionThroughDefinedModuleInterfaces
            */
        }

        requirement <SYSC_012> OrchestratorControlledExecution : ConstraintDefinitions::ImplementationConstraint {
            doc /*
            The MVP implementation shall use an orchestrator to call and coordinate processing modules.

            Rationale:
            The orchestrator provides the execution backbone for the MVP and allows different pipeline variants
            to be configured without embedding workflow logic into individual modules.

            Related system requirements:
            SYSR_030 SeparateControlFlowFromProcessingCapabilities
            SYSR_033 SupportConfigurablePipelineExecution
            */
        }

        requirement <SYSC_013> CanonicalJsonIntermediateRepresentation : ConstraintDefinitions::ImplementationConstraint {
            doc /*
            The MVP implementation shall use JSON as canonical intermediate representation.

            Rationale:
            JSON is not an expected legacy input format. It is an internal representation used after ingestion
            and extraction to provide a stable interface between processing steps.

            Related system requirements:
            SYSR_003 NormalizeToCanonicalJson
            SYSR_004 PreserveSourceMetadata
            */
        }
    }

    package UserInterfaceDesignConstraints {

        requirement <SYSC_014> UserInterfaceThroughOrchestrationInterface : ConstraintDefinitions::UserInterfaceConstraint {
            doc /*
            The user interface shall interact with processing capabilities through the orchestration interface.

            Rationale:
            The user interface is used for interaction, review and decision capture. Task specific processing logic
            shall remain in processing modules coordinated by the orchestrator.

            Related system requirements:
            SYSR_034 ProvideRudimentaryUserInterface
            SYSR_035 SupportFileUploadInUserInterface
            SYSR_036 PresentIngestionPreview
            SYSR_037 PresentReviewReportsInUserInterface
            SYSR_038 CaptureHumanReviewDecision
            SYSR_039 ProvideAccessToGeneratedSysMLv2Artifacts
            */
        }

        requirement <SYSC_015> RudimentaryMVPUserInterface : ConstraintDefinitions::UserInterfaceConstraint {
            doc /*
            The MVP user interface shall remain limited to interaction capabilities required for the proof of concept.

            Rationale:
            The user interface is included to demonstrate the human in the loop workflow and provide look and feel,
            but it shall not become the main development focus of the MVP.

            Related system requirements:
            SYSR_034 ProvideRudimentaryUserInterface
            SYSR_037 PresentReviewReportsInUserInterface
            SYSR_038 CaptureHumanReviewDecision
            */
        }
    }
}