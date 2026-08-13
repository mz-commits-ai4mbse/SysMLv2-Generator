package J1_Dependency_Syntax_Fixture {
    part def SourceType;
    part def TargetType;

    part source : SourceType;
    part target : TargetType;

    dependency from source to target;
}
