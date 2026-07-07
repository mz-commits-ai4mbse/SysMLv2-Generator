package '01_Stakeholder::01_Requirements::02_StakeholderRequirements' {
    
    public import '01_Stakeholder::01_Requirements::00_RequirementDefinitions'::*;
    public import '01_Stakeholder::01_Requirements::01_UserNeeds'::*;

    package '01_FunctionalRequirements' {
        requirement <SR_001> : FunctionalStakeholderRequirement {
            doc /* The system shall automatically synthesize a valid SysML v2 target model from heterogeneous legacy data fragments. */
            dependency from SR_001 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_006;
        }
        requirement <SR_002> : FunctionalStakeholderRequirement {
            doc /* The system shall use an ensemble of specialized generative agents to process parsed engineering fragments. */
            dependency from SR_002 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_006;
        }
        requirement <SR_003> : FunctionalStakeholderRequirement {
            doc /* The system shall implement an expert verification workspace for reviewing and editing synthesized architectural content. */
            dependency from SR_003 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_015;
            dependency from SR_003 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_02_004;
        }
        requirement <SR_004> : FunctionalStakeholderRequirement {
            doc /* The system shall automatically quantify and isolate ambiguities or low-confidence generation boundaries during synthesis. */
            dependency from SR_004 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_011;
            dependency from SR_004 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_02_001;
        }
        requirement <SR_005> : FunctionalStakeholderRequirement {
            doc /* Domain experts shall be provided with a specialized graphical user interface to review AI-generated architectural hypotheses. */
            dependency from SR_005 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_012;
            dependency from SR_005 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_02_002;
        }
        requirement <SR_006> : FunctionalStakeholderRequirement {
            doc /* The orchestration pipeline shall contain manual decision gates requiring expert intervention when severe data conflicts occur. */
            dependency from SR_006 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_013;
            dependency from SR_006 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_02_003;
        }
        requirement <SR_007> : FunctionalStakeholderRequirement {
            doc /* The system shall expose clear explainability data explaining the architectural patterns and rationale used for specific synthesis steps. */
            dependency from SR_007 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_014;
        }
        requirement <SR_008> : FunctionalStakeholderRequirement {
            doc /* Synthesized structural configurations must be explicitly committed by an authorized modeler before target repository storage. */
            dependency from SR_008 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_015;
            dependency from SR_008 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_02_004;
        }
    }

    package '02_DataQuality' {
        requirement <SR_009> : DataQualityStakeholderRequirement {
            doc /* The system shall automatically assess the machine readability and syntax validity of legacy data sources before synthesis. */
            dependency from SR_009 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_002;
        }
        requirement <SR_010> : DataQualityStakeholderRequirement {
            doc /* Every ingested legacy fragment shall be evaluated for information quality and assigned a standardized reliability score. */
            dependency from SR_010 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_003;
            dependency from SR_010 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_002;
        }
        requirement <SR_011> : DataQualityStakeholderRequirement {
            doc /* The system shall automatically identify incomplete or inconsistent input data structures before initiating model generation. */
            dependency from SR_011 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_004;
            dependency from SR_011 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_003;
        }
        requirement <SR_012> : DataQualityStakeholderRequirement {
            doc /* Predefined data quality criteria and validation rules shall guide the source data classification and filtering process. */
            dependency from SR_012 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_001;
        }
        requirement <SR_013> : DataQualityStakeholderRequirement {
            doc /* The system shall evaluate the reliability and semantic relevance of source engineering data before initiating the synthesis process. */
            dependency from SR_013 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_003;
            dependency from SR_013 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_002;
        }
    }

    package '03_ArchitecturalQuality' {
        requirement <SR_014> : ArchitecturalStakeholderRequirement {
            doc /* Synthesized system structures shall enforce strict separation of concerns through standardized namespaces and package dependencies. */
            dependency from SR_014 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_010;
            dependency from SR_014 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_03_001;
        }
        requirement <SR_015> : ArchitecturalStakeholderRequirement {
            doc /* Generated component definitions shall expose explicit, typed interface ports to enforce architectural compatibility. */
            dependency from SR_015 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_03_003;
        }
        requirement <SR_016> : ArchitecturalStakeholderRequirement {
            doc /* The synthesis engine shall automatically apply reusable architectural patterns from a validated reference library. */
            dependency from SR_016 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_03_007;
        }
        requirement <SR_017> : ArchitecturalStakeholderRequirement {
            doc /* Generated model content shall consistently conform to the systemic constraints defined by the global system architecture. */
            dependency from SR_017 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_03_006;
        }
        requirement <SR_018> : ArchitecturalStakeholderRequirement {
            doc /* Synthesized architectural elements shall enforce modularity and structural separation using standardized namespaces and interface definitions. */
            dependency from SR_018 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_010;
            dependency from SR_018 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_03_001;
            dependency from SR_018 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_03_003;
        }
    }

    package '04_Assurance' {
        requirement <SR_019> : AssuranceStakeholderRequirement {
            doc /* Modeler actions and automated translation steps shall be recorded in an immutable log to ensure process auditability. */
            dependency from SR_019 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_020;
        }
        requirement <SR_020> : AssuranceStakeholderRequirement {
            doc /* Automated model synthesis shall enforce formal syntactic validation against the KerML metamodel definition. */
            dependency from SR_020 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_021;
        }
        requirement <SR_021> : AssuranceStakeholderRequirement {
            doc /* The system shall guarantee complete vertical traceability by logging the relationship between every synthesized model element and its originating source data fragment. */
            dependency from SR_021 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_019;
            dependency from SR_021 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_006;
        }
        requirement <SR_022> : AssuranceStakeholderRequirement {
            doc /* The system shall guarantee vertical traceability by logging persistent links from every synthesized model element back to its source fragment. */
            dependency from SR_022 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_019;
            dependency from SR_022 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_006;
        }
    }

    package '05_SemanticConsistency' {
        requirement <SR_023> : SemanticStakeholderRequirement {
            doc /* All extracted information fragments shall be mapped to a standardized technical vocabulary to prevent semantic conflicts. */
            dependency from SR_023 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_016;
            dependency from SR_023 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_005;
        }
        requirement <SR_024> : SemanticStakeholderRequirement {
            doc /* Semantically equivalent elements originating from different legacy files shall be consolidated into single unified definitions. */
            dependency from SR_024 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_017;
            dependency from SR_024 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_02_007;
        }
        requirement <SR_025> : SemanticStakeholderRequirement {
            doc /* The system shall actively check for ontology and terminology conflicts prior to merging submodel packages. */
            dependency from SR_025 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_018;
            dependency from SR_025 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_004;
        }
        requirement <SR_026> : SemanticStakeholderRequirement {
            doc /* Extracted concepts and interface definitions shall be aligned with a standardized ontology to prevent domain terminology conflicts. */
            dependency from SR_026 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_01_016;
            dependency from SR_026 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_02_007;
            dependency from SR_026 to '01_Stakeholder::01_Requirements::01_UserNeeds'::UN_04_005;
        }
    }
}