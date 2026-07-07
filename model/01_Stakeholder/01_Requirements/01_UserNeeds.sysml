package '01_Stakeholder::01_Requirements::01_UserNeeds' {
    
    public import '01_Stakeholder::01_Requirements::00_RequirementDefinitions'::*;
    public import '01_Stakeholder::00_Stakeholders'::*;

    package '01_DataAssessment' {
        requirement <UN_01_001> : UserNeed {
            doc /* The user needs to identify which legacy data sources are suitable for automated processing. */
            dependency from UN_01_001 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_002> : UserNeed {
            doc /* The user needs to assess the machine readability of heterogeneous engineering data. */
            dependency from UN_01_002 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_003> : UserNeed {
            doc /* The user needs to distinguish between reliable and unreliable source information. */
            dependency from UN_01_003 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_004> : UserNeed {
            doc /* The user needs to identify incomplete or inconsistent input data before model synthesis begins. */
            dependency from UN_01_004 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_005> : UserNeed {
            doc /* The user needs to understand which input constraints are violated by provided legacy data. */
            dependency from UN_01_005 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
    }

    package '02_ModelSynthesis' {
        requirement <UN_01_006> : UserNeed {
            doc /* The user needs to transform heterogeneous legacy data into SysML v2 model structures. */
            dependency from UN_01_006 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_007> : UserNeed {
            doc /* The user needs generated model content to follow a consistent structural pattern. */
            dependency from UN_01_007 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_008> : UserNeed {
            doc /* The user needs generated model elements to remain reusable across different modeling contexts. */
            dependency from UN_01_008 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_009> : UserNeed {
            doc /* The user needs generated submodels to be integrated without restructuring existing model elements. */
            dependency from UN_01_009 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_010> : UserNeed {
            doc /* The user needs generated model structures to remain modular during iterative model growth. */
            dependency from UN_01_010 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
    }

    package '03_AmbiguityHandling' {
        requirement <UN_01_011> : UserNeed {
            doc /* The user needs to identify ambiguities during automated model synthesis. */
            dependency from UN_01_011 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_012> : UserNeed {
            doc /* The user needs to review AI-generated architectural assumptions before integration. */
            dependency from UN_01_012 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_013> : UserNeed {
            doc /* The user needs to intervene when conflicting interpretations of source data occur. */
            dependency from UN_01_013 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_014> : UserNeed {
            doc /* The user needs to understand why the system generated a specific modeling decision. */
            dependency from UN_01_014 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_015> : UserNeed {
            doc /* The user needs to validate generated model content before it becomes part of the target architecture. */
            dependency from UN_01_015 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
    }

    package '04_SemanticConsistency' {
        requirement <UN_01_016> : UserNeed {
            doc /* The user needs extracted information to follow a consistent technical vocabulary. */
            dependency from UN_01_016 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_017> : UserNeed {
            doc /* The user needs semantically equivalent information from different sources to be interpreted consistently. */
            dependency from UN_01_017 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_018> : UserNeed {
            doc /* The user needs ontology conflicts to be identified before model integration occurs. */
            dependency from UN_01_018 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
    }

    package '05_Traceability' {
        requirement <UN_01_019> : UserNeed {
            doc /* The user needs to trace generated model content back to its originating source data. */
            dependency from UN_01_019 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_020> : UserNeed {
            doc /* The user needs to understand which source information influenced generated model elements. */
            dependency from UN_01_020 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
        requirement <UN_01_021> : UserNeed {
            doc /* The user needs confidence that integrated submodels remain internally consistent. */
            dependency from UN_01_021 to '01_Stakeholder::00_Stakeholders'::SystemModeler;
        }
    }

    package '06_AmbiguityResolution' {
        requirement <UN_02_001> : UserNeed {
            doc /* The user needs to identify ambiguities in legacy engineering data. */
            dependency from UN_02_001 to '01_Stakeholder::00_Stakeholders'::DomainExpert;
        }
        requirement <UN_02_002> : UserNeed {
            doc /* The user needs to review AI-generated interpretations of domain-specific information. */
            dependency from UN_02_002 to '01_Stakeholder::00_Stakeholders'::DomainExpert;
        }
        requirement <UN_02_003> : UserNeed {
            doc /* The user needs to provide clarifications when source information is incomplete or contradictory. */
            dependency from UN_02_003 to '01_Stakeholder::00_Stakeholders'::DomainExpert;
        }
    }

    package '07_Validation' {
        requirement <UN_02_004> : UserNeed {
            doc /* The user needs to validate whether generated model content correctly reflects domain knowledge. */
            dependency from UN_02_004 to '01_Stakeholder::00_Stakeholders'::DomainExpert;
        }
        requirement <UN_02_005> : UserNeed {
            doc /* The user needs to identify incorrect assumptions in synthesized model structures. */
            dependency from UN_02_005 to '01_Stakeholder::00_Stakeholders'::DomainExpert;
        }
    }

    package '08_KnowledgePreservation' {
        requirement <UN_02_006> : UserNeed {
            doc /* The user needs implicit engineering knowledge to be reflected in the generated model. */
            dependency from UN_02_006 to '01_Stakeholder::00_Stakeholders'::DomainExpert;
        }
        requirement <UN_02_007> : UserNeed {
            doc /* The user needs domain terminology to be interpreted consistently across heterogeneous source data. */
            dependency from UN_02_007 to '01_Stakeholder::00_Stakeholders'::DomainExpert;
        }
    }

    package '09_ArchitectureQuality' {
        requirement <UN_03_001> : UserNeed {
            doc /* The user needs generated model structures to remain modular during system growth. */
            dependency from UN_03_001 to '01_Stakeholder::00_Stakeholders'::SystemArchitect;
        }
        requirement <UN_03_002> : UserNeed {
            doc /* The user needs independently generated submodels to be integrated without architectural restructuring. */
            dependency from UN_03_002 to '01_Stakeholder::00_Stakeholders'::SystemArchitect;
        }
        requirement <UN_03_003> : UserNeed {
            doc /* The user needs generated architectures to maintain consistent interface definitions. */
            dependency from UN_03_003 to '01_Stakeholder::00_Stakeholders'::SystemArchitect;
        }
    }

    package '10_ConsistencyAndIntegration' {
        requirement <UN_03_004> : UserNeed {
            doc /* The user needs architectural inconsistencies between integrated model elements to be identified. */
            dependency from UN_03_004 to '01_Stakeholder::00_Stakeholders'::SystemArchitect;
        }
        requirement <UN_03_005> : UserNeed {
            doc /* The user needs synthesized model structures to remain compatible with larger system contexts. */
            dependency from UN_03_005 to '01_Stakeholder::00_Stakeholders'::SystemArchitect;
        }
    }

    package '11_ArchitecturalGovernance' {
        requirement <UN_03_006> : UserNeed {
            doc /* The user needs architectural constraints to be consistently reflected in generated model content. */
            dependency from UN_03_006 to '01_Stakeholder::00_Stakeholders'::SystemArchitect;
        }
        requirement <UN_03_007> : UserNeed {
            doc /* The user needs reusable architectural patterns to be applied consistently across generated models. */
            dependency from UN_03_007 to '01_Stakeholder::00_Stakeholders'::SystemArchitect;
        }
    }

    package '12_InformationQuality' {
        requirement <UN_04_001> : UserNeed {
            doc /* The user needs to define quality criteria for legacy engineering data. */
            dependency from UN_04_001 to '01_Stakeholder::00_Stakeholders'::'Information Manager';
        }
        requirement <UN_04_002> : UserNeed {
            doc /* The user needs to classify source information according to reliability and relevance. */
            dependency from UN_04_002 to '01_Stakeholder::00_Stakeholders'::'Information Manager';
        }
        requirement <UN_04_003> : UserNeed {
            doc /* The user needs to identify source information that violates defined information quality rules. */
            dependency from UN_04_003 to '01_Stakeholder::00_Stakeholders'::'Information Manager';
        }
    }

    package '13_SemanticGovernance' {
        requirement <UN_04_004> : UserNeed {
            doc /* The user needs to define semantic rules for interpreting heterogeneous source data. */
            dependency from UN_04_004 to '01_Stakeholder::00_Stakeholders'::'Information Manager';
        }
        requirement <UN_04_005> : UserNeed {
            doc /* The user needs to maintain a standardized technical vocabulary for model synthesis. */
            dependency from UN_04_005 to '01_Stakeholder::00_Stakeholders'::'Information Manager';
        }
    }

    package '14_Traceability' {
        requirement <UN_04_006> : UserNeed {
            doc /* The user needs to ensure that model relevant information remains traceable to its originating source. */
            dependency from UN_04_006 to '01_Stakeholder::00_Stakeholders'::'Information Manager';
        }
    }
}