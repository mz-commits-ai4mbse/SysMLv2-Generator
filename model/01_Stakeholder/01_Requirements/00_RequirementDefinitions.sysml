package '01_Stakeholder::01_Requirements::00_RequirementDefinitions' {
    
    // Die Basis-Definition hält die Attribute 'rationale' und 'source' für alle bereit
    requirement def BaseRequirement {
        attribute rationale;
        attribute source;
    }
    
    // Diese Klassen erben direkt alle Attribute von BaseRequirement
    requirement def UserNeed :> BaseRequirement;
    
    requirement def StakeholderRequirements :> BaseRequirement;
    
    // Diese Klassen erben die Attribute nahtlos über StakeholderRequirements
    requirement def FunctionalStakeholderRequirement :> StakeholderRequirements;
    
    requirement def ArchitecturalStakeholderRequirement :> StakeholderRequirements;
    
    requirement def DataQualityStakeholderRequirement :> StakeholderRequirements;
    
    requirement def AssuranceStakeholderRequirement :> StakeholderRequirements;
    
    requirement def SemanticStakeholderRequirement :> StakeholderRequirements;
    
    requirement def OrganizationalStakeholderRequirement :> StakeholderRequirements;
}