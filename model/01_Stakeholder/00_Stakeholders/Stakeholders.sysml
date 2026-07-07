package '01_Stakeholder::00_Stakeholders' {
    
    public import '01_Stakeholder::01_Requirements::01_UserNeeds'::*;

    part def HumanRole;

    part def <ACT_01> SystemModeler :> HumanRole {
        doc /* Human role responsible for formal model creation, structural modeling, metadata ingestion and traceability logging. */
        attribute BasedOnRole {
            doc /* Modeler */
        }
    }
    
    part def <ACT_02> DomainExpert :> HumanRole {
        doc /* Human role providing domain-specific engineering knowledge to guide model synthesis, clarify ambiguities and validate generated content. */
        attribute BasedOnRole {
            doc /* Stakeholder Interface Manager plus domain specific validation responsibility */
        }
    }
    
    part def <ACT_03> SystemArchitect :> HumanRole {
        doc /* Human role providing product specific and domain specific knowledge to clarify ambiguous legacy data, validate assumptions and resolve domain conflicts. */
        attribute BasedOnRole {
            doc /* Stakeholder Interface Manager plus domain specific validation responsibility */
        }
    }
    
    part def <ACT_04> 'Information Manager' :> HumanRole {
        doc /* Human role responsible for information quality, source reliability, semantic consistency, ontology related rules and governance of model relevant information. */
        attribute BasedOnRole {
            doc /* IM */
        }
    }
}