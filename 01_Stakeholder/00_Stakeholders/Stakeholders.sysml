package Stakeholders {
    
    /* Human Actors */
    part def 'Consultant' {
        doc /* Primary user who initiates the synthesis process and manages the consulting project. */
    }

    part def 'DomainEngineer' {
        doc /* Subject matter expert providing implicit knowledge and validating physical constraints. */
    }

    /* System Components (KI als Block/Part definiert) */
    part def 'AISynthesisAgent' {
        doc /* The generative core utilizing LLMs (via AI Studio API) to synthesize SysML v2 code.[cite: 1] */
    }

    /* Organizational Stakeholder */
    part def 'ConsultingFirm' {
        doc /* The legal entity/client interested in efficiency gains through automated MBSE.[cite: 1] */
    }
}