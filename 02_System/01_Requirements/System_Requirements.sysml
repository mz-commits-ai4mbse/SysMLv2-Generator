package SystemRequirements {
    public import Requirements::*;
    import StakeholderRequirements::*;

    /* --- DATA LAYER --- */

    requirement <'SYS_RQ_1'> 'Multi-Format Parsing' {
        doc /* The system shall implement specialized parsers for Excel (.xlsx), PDF, and CAD metadata to extract raw feature fragments. */
        refine SR_1;
    }

    requirement <'SYS_RQ_2'> 'Source Reliability Scoring' {
        doc /* The Ingestion Agent shall assign a reliability metadata tag to each extracted fragment based on the source origin. */
        refine SR_6;
    }

    requirement <'SYS_RQ_3'> 'Initial Quality Assessment' {
        doc /* The Sorting Agent shall evaluate the completeness of ingested data and flag fragments with insufficient technical detail. */
        refine SR_4;
    }

    /* --- PROCESS LAYER --- */

    requirement <'SYS_RQ_4'> 'Autonomous Task Allocation' {
        doc /* The Orchestrator shall dynamically invoke specialized agents based on the classification result of the Sorting Agent[cite: 1]. */
        refine SR_1;
    }

    requirement <'SYS_RQ_5'> 'Ontological Mapping' {
        doc /* The Ontology Agent shall map local terminology to a central KerML-based domain ontology to ensure semantic alignment[cite: 1]. */
        refine SR_7;
    }

    requirement <'SYS_RQ_6'> 'Heuristic Pattern Application' {
        doc /* The Pattern Agent shall suggest missing system boundaries and port definitions based on a library of architectural templates[cite: 1]. */
        refine SR_3;
    }

    /* --- KNOWLEDGE LAYER --- */

    requirement <'SYS_RQ_7'> 'Automated Conflict Arbitration' {
        doc /* The Knowledge Layer shall resolve contradictory attributes by applying the source prioritization matrix[cite: 1]. */
        refine SR_6;
        refine SR_5;
    }

    requirement <'SYS_RQ_8'> 'Modular Namespace Generation' {
        doc /* The Synthesis Agent shall wrap each sub-model in a unique SysML v2 namespace to prevent naming collisions during integration[cite: 1]. */
        refine SR_2;
    }

    requirement <'SYS_RQ_9'> 'Interface Usage Synthesis' {
        doc /* The system shall generate explicit 'usage' elements for all anticipated ports to allow late-binding in the architecture[cite: 1]. */
        refine SR_2;
        refine SR_3;
    }

    requirement <'SYS_RQ_10'> 'Grammar Conformance Check' {
        doc /* The Validation Agent shall perform a syntax check against the SysML v2 / KerML EBNF grammar before outputting code[cite: 1]. */
        refine SR_1;
        refine SR_5;
    }

    /* --- HUMAN-IN-THE-LOOP & ORCHESTRATION --- */

    requirement <'SYS_RQ_11'> 'Expert Override Mechanism' {
        doc /* The Orchestrator shall halt execution and request manual input if the AI confidence score for a synthesis step falls below a defined threshold[cite: 1]. */
        refine SR_4;
    }

    requirement <'SYS_RQ_12'> 'Global Consistency Tracking' {
        doc /* The Knowledge Layer shall maintain a global dependency graph to track the impact of manual changes on automated synthesis results[cite: 1]. */
        refine SR_5;
    }
}