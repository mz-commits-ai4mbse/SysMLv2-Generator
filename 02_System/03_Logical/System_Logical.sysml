package SystemLogical {
    import Stakeholders::*;
    import SystemFunctions::*;
    import SystemRequirements::*;

    /* Interface Definitions */
    port def AgentDataPort;
    port def KnowledgeAccessPort;
    port def UserInteractionPort;

    part def 'AiC_Generator_System' {
        
        // --- Infrastructure & Management ---
        part orchestrator : 'OrchestratorUnit' {
            port blackboardAccess : AgentDataPort;
            port uiLink : UserInteractionPort;
        }
        
        part blackboard : 'GlobalBlackboard' {
            port dataIn : AgentDataPort;
            port dataOut : AgentDataPort;
        }

        part expertDashboard : 'UserInterface' {
            port userIn : UserInteractionPort;
        }

        // --- Data Layer Experts ---
        part ingestionAgent : 'IngestionExpert' {
            port rawOut : AgentDataPort;
        }
        
        part slicingAgent : 'SlicingExpert' {
            port sliceLink : AgentDataPort;
        }

        // --- Process Layer (The Agent Ensemble) ---
        /* Representing multiple specialized personas as an ensemble */
        part agentEnsemble : 'SynthesisExpert' [3] {
            port bbLink : AgentDataPort;
            port kbQuery : KnowledgeAccessPort;
        }

        // --- Knowledge Layer Experts ---
        part ontologyAgent : 'OntologyExpert' {
            port bbLink : AgentDataPort;
            port dbQuery : KnowledgeAccessPort;
        }

        part varianceMonitor : 'QualityExpert' {
            port checkLink : AgentDataPort;
        }

        // --- Knowledge Bases (Databases) ---
        part ontologyDB : 'DomainOntologyDB' {
            port queryPort : KnowledgeAccessPort;
        }

        /* Allocations: Mapping Functions to Logic */
        allocate action SystemFunctions::OrchestratedSynthesisProcess::ExecuteMultiFormatParsing to ingestionAgent;
        allocate action SystemFunctions::OrchestratedSynthesisProcess::FragmentDataSlices to slicingAgent;
        allocate action SystemFunctions::OrchestratedSynthesisProcess::ExecuteMultiAgentEnsemble to agentEnsemble;
        allocate action SystemFunctions::OrchestratedSynthesisProcess::CalculateResultVariance to varianceMonitor;
        allocate action SystemFunctions::OrchestratedSynthesisProcess::UpdateVarianceDashboard to expertDashboard;
    }

    /* Logical Definitions for the new Experts */
    part def 'SlicingExpert' {
        doc /* Expert for breaking down JSON data into smaller context-aware slices. */
    }
    
    part def 'QualityExpert' {
        doc /* Expert for statistical variance analysis between agent results. */
    }
    
    part def 'UserInterface' {
        doc /* Graphical interface for expert reporting and decision gates. */
    }

    part def 'SynthesisExpert';
}