# Gridfinity Reference

## What is Gridfinity?

Gridfinity is an open-source, modular grid storage system for 3D printing. Created by Zack Freedman and released under MIT license, it enables endless customization for organizing tools, parts, and supplies.

## Core Specifications

### Grid System

- **Base unit**: 42mm x 42mm x 7mm (X x Y x Z)
- **Unit notation**: Dimensions expressed as multiples (e.g., "2x3x4u" = 84mm x 126mm x 28mm)
- **Height unit**: 1u = 7mm
- **Stacking lip**: Optional 4.4mm addition to height

### Bin Dimensions

- **Actual bin size**: 41.5mm x 41.5mm (0.5mm total tolerance for fit)
- **Tolerance**: 0.25mm per side
- **Corner radius**: 3.75mm (filleted edges)
- **First layer**: 4.75-5.0mm used for base (leaves 2.0-2.25mm usable space in first 7mm)

### Baseplate

- **Grid squares**: 42mm x 42mm each
- **Socket**: Z-shaped profile holds bins securely while allowing easy reconfiguration
- **Spacing**: Multiple bins have 0.5mm gap between bases (aligned at 42mm centers)

### Optional Features

**Magnets:**

- Standard size: 6mm diameter x 2mm thickness
- Placement: Four corners of each grid unit
- Purpose: Secure bins to steel surfaces or magnetic baseplates
- Alternative: M3 screws in corners for non-magnetic setup

**Labels:**

- Shelf at top of bin (below stacking lip)
- Typically 45Â° slope on bottom (no supports needed)
- No standardized size/shape
- Doubles as finger grip for lifting

## Key Design Principles

- Universal compatibility over proprietary designs
- Modularity and beauty
- Open standards, not walled gardens
- Multiple of 7mm for maximum divisibility
- MIT licensed (free to use, modify, share)

## Official Resources

**Specification & Documentation:**

- Official spec: <https://gridfinity.xyz/specification/>
- Unofficial GitHub spec: <https://github.com/gridfinity-unofficial/specification>
- Community wiki: <https://gridfinity.xyz/>

**Design Tools:**

- Gridfinity Generator (online): <https://gridfinitygenerator.com/>
- Layout calculator: <https://gridfinitylayout.com/>
- FreeCAD Gridfinity Workbench: <https://github.com/Stu142/FreeCAD-Gridfinity-Workbench>

**Original Video:**

- Zack Freedman's introduction: <https://www.youtube.com/watch?v=ra_9zU-mnl8>

**Community:**

- Discord: #gridfinity channel on Zack's Void Star Lab server

## Compatibility Notes

- Most designs use 41.5mm bin dimensions for proper fit
- Some variations exist (35.7mm, 37.7mm) - stick to standard 41.5mm
- Bins with labels: Check clearance if stacking
- Magnetic polarity: Keep consistent across collection if using magnetic baseplates

## Common Variations

- **Vase mode bins**: Spiral wall printing for speed
- **Weighted baseplates**: Added mass for desktop stability
- **Stackable baseplates**: Can layer on top of filled bins
- **Integrated handles**: For portable baseplate systems
- **Toolbox configurations**: Drawer systems using Gridfinity standard

## Measuring Your Prints

- External baseplate dimensions = N x 42mm (where N = grid units)
- Bin internal dimensions = actual usable space (varies by wall thickness)
- Height without lip = N x 7mm
- Height with lip = (N x 7mm) + 4.4mm

## Related Systems (from home organization framework)

- **Neogrid**: For large items in drawers
- **openGrid**: Wall-mounted, small items
- **French Cleat**: Heavy wall items
- **Underware**: Cable management

______________________________________________________________________

*Last updated: October 2025*
*System: Gridfinity v1 (Community Standard)*
