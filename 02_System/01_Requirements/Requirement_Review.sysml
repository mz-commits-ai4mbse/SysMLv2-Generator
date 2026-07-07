package RequirementReview {
    /* 1. Importiere die Pakete mit ihrem vollqualifizierten Namen */
    import StakeholderRequirements::*;
    import SystemRequirements::*;

    view RequirementTraceabilityMatrix {
        doc /* Visualisierung der Refine-Beziehungen für das Review. */
        
        /* Filter-Logik für die Matrix */
        filter {
            // Wir filtern auf alle Requirements
            include feature StakeholderRequirements::*;
            include feature SystemRequirements::*;
        }
        
        /* Wir sagen dem Tool, welche Beziehungstypen wichtig sind */
        rendering {
            /* Hier wird definiert, wie die Elemente grafisch 
               oder tabellarisch verknüpft werden sollen */
        }
    }
}