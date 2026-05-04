package StakeholderLogical {
    import StakeholderUseCases::*;

    /* Abstract logical components of the stakeholder solution */
    part def GenerativeArchitectureEnvironment {
        part ingestionUnit : DataIngestionPort;
        part synthesisEngine : AISynthesisCore;
        part validationInterface : ExpertUI;
    }

    part def DataIngestionPort {
        doc /* Interface to accept heterogeneous legacy data (PDF, Excel, CAD). */
    }

    part def AISynthesisCore {
        doc /* The "Intelligence" that matches patterns and generates SysML v2 code.[cite: 1] */
    }

    part def ExpertUI {
        doc /* The interface where the Domain Engineer reviews and refines models.[cite: 1] */
    }
}