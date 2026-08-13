package J1_Satisfaction_Syntax_Fixture {
    part def ExampleSystem;

    requirement exampleRequirement {
        subject exampleSystem : ExampleSystem;
        doc /* The example system shall demonstrate requirement satisfaction syntax. */
    }

    part exampleSystem : ExampleSystem;

    satisfy exampleRequirement by exampleSystem;
}
