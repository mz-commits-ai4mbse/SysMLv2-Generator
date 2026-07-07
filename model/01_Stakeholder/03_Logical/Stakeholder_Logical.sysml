package TuringStakeholderLogicalContext {

    doc /*
    Purpose:
    This package documents the stakeholder logical context of the Turing Generator.

    Modeling status:
    Transitional SysIDE shadow model.
    The authoritative stakeholder requirements and use cases are currently stored in the CATIA Magic SoSA model.

    Scope:
    This view defines the system of interest, external human roles, external information sources, target environments and exchanged information objects.
    Internal agent architecture is intentionally excluded and will be modeled on system level.
    */

    part def TuringGenerator {
        doc /*
        System of interest.

        The Turing Generator processes heterogeneous legacy engineering data and supports the controlled generation of valid SysML v2 model structures.

        The system provides intermediate review reports, supports human approval decisions and generates SysIDE compatible SysML v2 output.
        */
    }

    part def HumanRole {
        doc /*
        Abstract human stakeholder role.
        Human roles are represented as external logical actors in the stakeholder context.
        */
    }

    part def SystemModeler :> HumanRole {
        doc /*
        Corresponds to ACT_01 in the CATIA model.

        Primary role:
        Operates the Turing Generator, reviews intermediate results and approves generated model content.
        */
    }

    part def DomainExpert :> HumanRole {
        doc /*
        Corresponds to ACT_02 in the CATIA model.

        Primary role:
        Clarifies ambiguous domain knowledge and validates domain specific interpretations.
        */
    }

    part def SystemArchitect :> HumanRole {
        doc /*
        Corresponds to ACT_03 in the CATIA model.

        Primary role:
        Validates architectural quality, modularity, interface consistency and integration suitability.
        */
    }

    part def InformationManager :> HumanRole {
        doc /*
        Corresponds to ACT_04 in the CATIA model.

        Primary role:
        Maintains information quality rules, semantic rules, ontology related constraints and technical vocabulary.
        */
    }

    part def LegacyDataSources {
        doc /*
        External sources containing heterogeneous legacy engineering data.

        Examples:
        Text documents, tables, requirement exports, existing design descriptions, interface notes and other machine readable Brownfield engineering artifacts.
        */
    }

    part def KnowledgeBase {
        doc /*
        External or maintained knowledge resource.

        Contains:
        Ontology and vocabulary
        Architecture constraints
        SysML v2 modeling rules
        Domain specific interpretation rules
        */
    }

    part def SysMLv2TemplateRepository {
        doc /*
        Public or project specific repository that provides the target SysIDE project structure and valid SysML v2 syntax examples.

        This repository acts as syntax reference for generated output.
        */
    }

    part def SysIDEValidationEnvironment {
        doc /*
        Target validation environment for generated SysML v2 files.

        The generated model output shall be valid in SysIDE.
        */
    }

    item def LegacyEngineeringData {
        doc /*
        Heterogeneous source information used as input for model generation.
        */
    }

    item def OntologyAndVocabulary {
        doc /*
        Semantic reference information used for terminology alignment and semantic consistency checks.
        */
    }

    item def ArchitectureConstraints {
        doc /*
        Architectural rules used to support modularity, interface consistency and integration suitability.
        */
    }

    item def ReviewReport {
        doc /*
        Human readable report that presents candidate results, differences between agent outputs, rationale, source references and required human decisions.
        */
    }

    item def ApprovedIntermediateResult {
        doc /*
        Human approved result of a processing step.
        This result becomes input for the subsequent processing step.
        */
    }

    item def GeneratedSysMLv2Model {
        doc /*
        Generated SysML v2 model content following the defined SysIDE compatible target notation.
        */
    }

    item def ValidationFeedback {
        doc /*
        Feedback from the SysIDE validation environment regarding syntactic or structural issues in generated SysML v2 files.
        */
    }

    doc /*
    Context relationships:

    LegacyDataSources provide LegacyEngineeringData to TuringGenerator.

    KnowledgeBase provides OntologyAndVocabulary and ArchitectureConstraints to TuringGenerator.

    SysMLv2TemplateRepository provides target project structure and syntax reference to TuringGenerator.

    SystemModeler operates TuringGenerator and approves intermediate results.

    DomainExpert clarifies ambiguous domain knowledge.

    SystemArchitect validates generated architecture quality.

    InformationManager governs semantic and information quality rules.

    TuringGenerator presents ReviewReport to human roles.

    TuringGenerator submits GeneratedSysMLv2Model to SysIDEValidationEnvironment.

    SysIDEValidationEnvironment returns ValidationFeedback to TuringGenerator.

    Traceability to CATIA model:
    ACT_01 SystemModeler
    ACT_02 DomainExpert
    ACT_03 SystemArchitect
    ACT_04 InformationManager
    UC_000 ReviewAndApproveStepResult
    UC_001 AssessLegacyData
    UC_002 PrepareDataForSynthesis
    UC_003 ApplySemanticGuardrails
    UC_004 ResolveAmbiguity
    UC_005 SynthesizeSysMLv2Model
    UC_006 ValidateGeneratedArchitecture
    */
}