package SystemFunctions {
    import SystemRequirements::*;
    import Stakeholders::*;

    action def 'OrchestratedSynthesisProcess' {
        
        // --- DATA LAYER ACTIONS (Säule 1, 3 & 4) ---
        action 'ParseLegacyData' {
            doc /* Extraction of raw features from Excel, PDF, and CAD. */
        }
        
        action 'NormalizeToJSON' {
            doc /* Conversion of extracted fragments into standardized JSON format. */
        }

        action 'PerformSourceReliabilityTagging' {
            doc /* Assignment of reliability scores based on source origin. */
        }

        action 'FragmentDataSlices' {
            doc /* Slicing of JSON data into context-preserving packages. */
        }

        // --- PROCESS LAYER ACTIONS (Säule 2) ---
        action 'DetermineAgentSequence' {
            doc /* Orchestrator allocates tasks based on data slice quality. */
        }

        action 'ExecuteMultiAgentEnsemble' {
            doc /* Parallel synthesis by multiple agents with different personas. */
        }

        action 'CalculateResultVariance' {
            doc /* Quantification of deviations between agent outputs. */
        }

        action 'MapToTechnicalOntology' {
            doc /* Alignment of terminology to the standardized vocabulary. */
        }

        action 'ProposeArchitecturalPatterns' {
            doc /* Anticipation of missing interfaces and structures. */
        }

        // --- KNOWLEDGE & INTERFACE LAYER ---
        action 'ResolveSemanticConflicts' {
            doc /* Rule-based arbitration of contradictory information. */
        }

        action 'UpdateVarianceDashboard' {
            doc /* Presentation of identical and deviating fragments in the UI. */
        }

        action 'RequestExpertValidation' {
            doc /* Manual decision gate for the domain engineer. */
        }

        action 'SynthesizeModularSysML' {
            doc /* Generation of final namespaces and usage elements. */
        }

        action 'ValidateGrammarAndConsistency' {
            doc /* Final check against KerML and dependency tracking. */
        }

        /* Logical Flow of the Orchestrator */
        flow from 'ParseLegacyData' to 'NormalizeToJSON';
        flow from 'NormalizeToJSON' to 'PerformSourceReliabilityTagging';
        flow from 'PerformSourceReliabilityTagging' to 'FragmentDataSlices';
        flow from 'FragmentDataSlices' to 'DetermineAgentSequence';
        flow from 'DetermineAgentSequence' to 'ExecuteMultiAgentEnsemble';
        flow from 'ExecuteMultiAgentEnsemble' to 'CalculateResultVariance';
        flow from 'CalculateResultVariance' to 'UpdateVarianceDashboard';
        flow from 'UpdateVarianceDashboard' to 'RequestExpertValidation';
        flow from 'RequestExpertValidation' to 'MapToTechnicalOntology';
        flow from 'MapToTechnicalOntology' to 'ProposeArchitecturalPatterns';
        flow from 'ProposeArchitecturalPatterns' to 'ResolveSemanticConflicts';
        flow from 'ResolveSemanticConflicts' to 'SynthesizeModularSysML';
        flow from 'SynthesizeModularSysML' to 'ValidateGrammarAndConsistency';
    }

    /* 100% Requirement Coverage (satisfy-links) */
    satisfy SYS_RQ_1 by 'ParseLegacyData';
    satisfy SYS_RQ_2 by 'NormalizeToJSON';
    satisfy SYS_RQ_3 by 'FragmentDataSlices';
    satisfy SYS_RQ_4 by 'ExecuteMultiAgentEnsemble';
    satisfy SYS_RQ_5 by 'CalculateResultVariance';
    satisfy SYS_RQ_6 by 'ProposeArchitecturalPatterns';
    satisfy SYS_RQ_7 by 'ResolveSemanticConflicts';
    satisfy SYS_RQ_8 by 'UpdateVarianceDashboard';
    satisfy SYS_RQ_9 by 'UpdateVarianceDashboard'; // Central UI
    satisfy SYS_RQ_10 by 'UpdateVarianceDashboard'; // Variance Reporting
    satisfy SYS_RQ_11 by 'RequestExpertValidation'; // Override Mechanism
    satisfy SYS_RQ_12 by 'UpdateVarianceDashboard'; // Graphical UI
    satisfy SYS_RQ_13 by 'UpdateVarianceDashboard'; // Variance Reporting Detail
    satisfy SYS_RQ_14 by 'RequestExpertValidation'; // Expert Decision Gate
    satisfy SYS_RQ_15 by 'ValidateGrammarAndConsistency'; // Traceability & Consistency
}