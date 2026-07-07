package SystemRequirements {
    public import Requirements::*;
    public import StakeholderRequirements::*;

    /* --- DATA LAYER (Säule 1 & 4) --- */

    requirement <'SYS_RQ_1'> 'Multi-Format Ingestion' {
        doc /* The system shall implement specialized parsers for Excel, PDF, and CAD metadata fragments. */
        refine StakeholderRequirements::SR_1;
    }

    requirement <'SYS_RQ_2'> 'JSON Normalization' {
        doc /* All ingested data fragments shall be normalized into a standardized JSON format to ensure interoperability. */
        refine StakeholderRequirements::SR_7;
    }

    requirement <'SYS_RQ_3'> 'Data Slicing' {
        doc /* The system shall fragment standardized data into small, context-preserving packages for reliable LLM processing. */
        refine StakeholderRequirements::SR_1;
    }

    requirement <'SYS_RQ_4'> 'Source Reliability Tagging' {
        doc /* Every data fragment shall be tagged with its source origin and a reliability score. */
        refine StakeholderRequirements::SR_6;
    }

    /* --- PROCESS LAYER (Säule 2) --- */

    requirement <'SYS_RQ_5'> 'Orchestrated Task Allocation' {
        doc /* The Orchestrator shall dynamically invoke specialized agents based on the data type and quality. */
        refine StakeholderRequirements::SR_1;
    }

    requirement <'SYS_RQ_6'> 'Multi-Agent Persona Ensemble' {
        doc /* Each synthesis task shall be processed by at least three agents with varying temperatures and skills. */
        refine StakeholderRequirements::SR_1;
    }

    requirement <'SYS_RQ_7'> 'Variance Quantification' {
        doc /* The system shall compute the statistical variance between results of the agent ensemble to assess reproducibility. */
        refine StakeholderRequirements::SR_5;
    }

    requirement <'SYS_RQ_8'> 'Pattern Matching' {
        doc /* Specialized agents shall use an architectural pattern library to anticipate missing system structures. */
        refine StakeholderRequirements::SR_3;
    }

    /* --- KNOWLEDGE LAYER (Säule 4) --- */

    requirement <'SYS_RQ_9'> 'Semantic Conflict Resolution' {
        doc /* Contradictory information shall be resolved using a rule-based prioritization matrix. */
        refine StakeholderRequirements::SR_6;
        refine StakeholderRequirements::SR_5;
    }

    requirement <'SYS_RQ_10'> 'Modular Code Synthesis' {
        doc /* The system shall generate SysML v2 code using namespaces and usages to ensure plug-and-play modularity. */
        refine StakeholderRequirements::SR_2;
    }

    requirement <'SYS_RQ_11'> 'Grammar Validation' {
        doc /* All generated SysML v2 fragments shall be validated against the formal KerML abstract syntax. */
        refine StakeholderRequirements::SR_1;
        refine StakeholderRequirements::SR_5;
    }

    /* --- INTERFACE & HUMAN-IN-THE-LOOP --- */

    requirement <'SYS_RQ_12'> 'Graphical User Interface' {
        doc /* The system shall provide a UI for managing data ingestion and reviewing synthesis results. */
        refine StakeholderRequirements::SR_4;
    }

    requirement <'SYS_RQ_13'> 'Variance Reporting' {
        doc /* The UI shall highlight differences and similarities between agent results for expert evaluation. */
        refine StakeholderRequirements::SR_4;
    }

    requirement <'SYS_RQ_14'> 'Expert Decision Gate' {
        doc /* The Orchestrator shall require manual confirmation before committing a low-confidence synthesis result. */
        refine StakeholderRequirements::SR_4;
    }

    requirement <'SYS_RQ_15'> 'Traceability Logging' {
        doc /* The system shall maintain a log linking every generated SysML v2 element back to its source data fragment. */
        refine StakeholderRequirements::SR_5;
    }
}