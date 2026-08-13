package J5_Relationship_Rendering_Syntax_Fixture {
    part IME_000001 {
        doc /* Engineering name: Source Component */
    }

    part IME_000002 {
        doc /* Engineering name: Target Component */
    }

    action IME_000003 {
        doc /* Engineering name: Source Function */
    }

    dependency from IME_000001 to IME_000002;

    allocate IME_000003 to IME_000002;
}
