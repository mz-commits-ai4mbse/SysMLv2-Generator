package StakeholderPhysical {
    import Stakeholders::*;
    import StakeholderLogical::*;

    /* Physical allocation of the generative environment */
    part architectureWorkstation {
        
        /* The IDE hosting the SysML v2 tooling */
        part vscodeEnvironment {
            doc /* Visual Studio Code with SysML v2 extension for textual modeling. */
        }

        /* The local execution environment */
        part pythonRuntime {
            doc /* Python environment executing the orchestrator and local agents. */
        }

        /* External AI Service */
        part aiStudioService {
            doc /* Remote API providing the LLM capabilities (Gemini 3 Flash). */
        }
    }

    /* Connection to the Actors */
    connection 'UI_Connection' {
        end 'consultantInstance' : 'Consultant';
        end 'vscodeEnvironment';
    }

    connection 'Expert_Review_Link' {
        end 'expertInstance' : 'DomainEngineer';
        end 'vscodeEnvironment';
    }
}