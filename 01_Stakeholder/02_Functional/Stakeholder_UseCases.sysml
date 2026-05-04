package StakeholderUseCases {
    import Stakeholders::*;

    use case 'Synthesize System Architecture' {
        doc /* Main goal: Automated generation of SysML v2 models. */
    }

    use case 'Validate Model Consistency' {
        doc /* Human-in-the-loop validation of the AI-generated structures.[cite: 1] */
    }

    /* Relationships between Actors and the AI Block */
    part 'consultantInstance' : 'Consultant';
    part 'expertInstance' : 'DomainEngineer';
    part 'aiAgent' : 'AISynthesisAgent';

    perform 'consultantInstance' {
        use case 'Synthesize System Architecture';
    }

    perform 'expertInstance' {
        use case 'Validate Model Consistency';
    }

    /* The AI Agent supports the use case execution */
    exhibit 'aiAgent' {
        use case 'Synthesize System Architecture';
    }
}