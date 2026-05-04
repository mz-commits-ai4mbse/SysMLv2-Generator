package StakeholderRequirements {
    public import Requirements::*;

    requirement <'SR_1'> 'Automated Model Synthesis' {
        doc /* The system shall automatically generate valid SysML v2 code from heterogeneous, unstructured legacy data. */
    }

    requirement <'SR_2'> 'Modular Architecture' {
        doc /* The generated models shall be structured as independent modules to allow non-destructive integration of new components.*/
    }

    requirement <'SR_3'> 'Interface Anticipation' {
        doc /* The system shall use architectural patterns to anticipate required interfaces (ports) not explicitly present in the source data.*/
    }

    requirement <'SR_4'> 'Expert Validation' {
        doc /* The system shall provide mechanisms for domain experts to validate and refine AI-generated architectural hypotheses. */
    }

    requirement <'SR_5'> 'Model Consistency' {
        doc /* The synthesis process shall ensure that integrated sub-models maintain overall system consistency. */
    }
}