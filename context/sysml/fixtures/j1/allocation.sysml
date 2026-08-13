package J1_Allocation_Syntax_Fixture {
    part def LogicalType;
    part def PhysicalType;

    part logicalElement : LogicalType;
    part physicalElement : PhysicalType;

    allocate logicalElement to physicalElement;
}
