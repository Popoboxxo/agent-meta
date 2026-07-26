# Deskware Reference

## What is Deskware?

Deskware is an open-source, modular desk riser and organizer system designed by Hands on Katie. It creates elevated platforms with integrated storage underneath, combining desk organization with cable management and grid-based accessories. Released under CC-BY-NC-SA license, it features parametric customization and native integration with Gridfinity and OpenGrid systems.

## Core Concept

**Elevated modular desk organization** - Deskware uses:

- **3D-printed risers** (customizable height, width, depth)
- **Modular top plates** (with optional Gridfinity/OpenGrid recesses)
- **HOK connectors** (stack risers vertically for multi-level setups)
- **Drawer integration** (optional drawer units within risers)
- **Curved sections** (parametric arc-based corner transitions)

## Core Specifications

### Riser System

- **Width**: Customizable in 84mm increments (2 Gridfinity units / 3 OpenGrid units)
- **Depth**: Customizable in 28mm increments (OpenGrid units)
- **Height**: Customizable in 40mm increments (67.5mm minimum)
- **End style**: Rounded, Squared, or Rounded Square
- **Material**: PLA or PETG recommended

### Top Plate Dimensions

- **Recess depth**: Customizable (0.1mm increments, default 1mm)
- **Lip width**: Adjustable border (default 0.5mm)
- **Grid alignment**: Matches Gridfinity (42mm) or OpenGrid (28mm) spacing
- **Overhang**: Extends beyond riser front for usable surface area

### HOK Connectors

- **Purpose**: Stack risers vertically to create multi-level platforms
- **Mounting**: Bottom of risers have HOK connector points
- **Compatibility**: Parametric sizing for different riser configurations
- **Design**: Interlocking male/female connectors for secure stacking

## Key Components

### Risers

- **Core section**: Main body of the riser (width, depth, height customizable)
- **Front chamfer**: Customizable front edge angle
- **Side slides**: Optional cutouts for side access
- **Split height option**: Divide tall risers into multiple printable sections
- **Bottom HOK mounts**: Integrated connector points for stacking

### Top Plates

- **Standard top**: Flat surface with optional recess
- **Gridfinity recess**: 42mm grid baseplate pockets
- **OpenGrid Lite recess**: 4mm thick board pockets (28mm grid)
- **OpenGrid Full recess**: 6.8mm thick board pockets (28mm grid)
- **Wireless charger mount**: Circular recess with cord channel

### Drawers (Optional)

- **Mounting options**: Printed handles or hardware screw holes (single/double)
- **Screw compatibility**: Customizable diameter (5mm common)
- **Height adjustment**: Vertical position of drawer pulls adjustable
- **Width**: Matches core section width

### Curved Sections

- **Arc customization**: Degrees of arc (parametric)
- **Radius**: Customizable curve radius
- **Use case**: Corner desk transitions, smooth directional changes
- **Integration**: Compatible with straight sections

## Print Settings

- **Layer height**: 0.2mm
- **Walls**: 3-4 walls recommended
- **Infill**: 15-20%
- **Material**: PLA or PETG
- **Supports**: May be needed for curved sections and overhangs
- **Split printing**: Large risers can be split at height intervals

## Design Principles

- Modular elevation with grid integration
- Parametric customization for any desk layout
- Native Gridfinity and OpenGrid compatibility
- Stackable architecture via HOK connectors
- Cable management through/under risers
- Living room compatible aesthetics
- Open-source and extensible (CC-BY-NC-SA)

## Official Resources

**Main Documentation:**

- QuackWorks repository: <https://github.com/AndyLevesque/QuackWorks/tree/main/Deskware>
- Hands on Katie: <https://handsonkatie.com/>

**Downloads:**

- MakerWorld: Search "Deskware" (parametric customizer available)
- QuackWorks GitHub: Direct OpenSCAD source files

**Related Systems:**

- Gridfinity: <https://gridfinity.xyz/>
- OpenGrid: <https://www.opengrid.world/>
- Underware: <https://handsonkatie.com/underware-2-0-the-made-to-measure-collection/>

**Contributors:**

- Hands on Katie (original designer)
- BlackjackDuck (Andy) - OpenSCAD implementation
- David D - OpenGrid integration
- Community via QuackWorks GitHub

## Common Use Cases

- Monitor risers with storage underneath
- Keyboard platforms with cable routing
- Corner desk organizers with curved sections
- Multi-level desk platforms (stacked risers)
- Desk-integrated Gridfinity bins (recessed top plates)
- Elevated printer stations with tool storage
- Standing desk accessory platforms

## Setup Quick Reference

1. **Determine dimensions**: Measure desk area and desired elevation
2. **Choose top plate style**: Flat, Gridfinity recess, OpenGrid recess, or wireless charger
3. **Customize in OpenSCAD**: Adjust width, depth, height, end style
4. **Print risers**: Split tall sections if needed for bed size
5. **Print top plate**: With selected recess pattern
6. **Print HOK connectors**: If stacking multiple levels
7. **Assemble**: Stack risers using HOK connectors, attach top plate
8. **Add accessories**: Insert Gridfinity bins or OpenGrid items as configured

## Customization

### Key Parameters (from Deskware_Main.scad)

**Core Section:**

- `Core_Section_Width`: 196mm default (84mm increments)
- `Core_Section_Depth`: 196.5mm default (84mm increments)
- `Total_Height`: 107.5mm default (40mm increments)

**End Style:**

- `End_Style`: "Rounded", "Squared", or "Rounded Square"
- `Rounded_Square_Rounding`: 50mm default radius

**Top Plate:**

- `Top_Plate_Recess`: 1mm default depth
- `Top_Plate_Lip_Width`: 0.5mm default border
- `Enable_Top_Plate_Customizer`: false/true
- `Top_Plate_Customization`: "Gridfinity Top", "openGrid Lite Top", "openGrid Full Top", "Wireless Charger"

**Curved Sections:**

- `Enable_Curve_Mode`: false/true
- `Degrees_of_Arc`: 45° default

**Wireless Charger:**

- `Wireless_Charger_Diameter`: 50mm default
- `Wireless_Charger_Thickness`: 8mm default
- `Wireless_Charger_Cord_Width`: 6mm
- `Wireless_Charger_Cord_Length_Outward`: 14mm

## Integration Points

### Gridfinity Compatibility

- **Top plate recesses**: Hold Gridfinity baseplate sections flush
- **Grid alignment**: 42mm spacing matches Gridfinity standard
- **Bin placement**: Desktop organization directly on riser surface
- **Stacking**: Gridfinity bins work above/around Deskware platforms

### OpenGrid Compatibility

- **Lite board recesses**: 4mm thickness, 28mm grid spacing
- **Full board recesses**: 6.8mm thickness, 28mm grid spacing
- **Wall integration**: OpenGrid boards can mount behind Deskware setups
- **Snap accessories**: OpenGrid items attach to recessed boards

### Underware Compatibility

- **Cable routing**: Channels route through/under elevated risers
- **OpenGrid base**: Mount OpenGrid under desk, snap Underware, place Deskware above
- **Height advantage**: Elevated platforms create space for cable management
- **Integrated workflow**: Deskware risers + Underware channels + OpenGrid backing

### French Cleat Compatibility

- **Indirect integration**: Wall-mounted cleats work alongside desk risers
- **Tool walls**: Cleats behind desk + Deskware on desk surface
- **No direct connection**: Systems serve different mounting surfaces

## Troubleshooting

- **Riser too tall for printer**: Use split height option to print in sections
- **Top plate recess too shallow**: Increase `Top_Plate_Recess` parameter
- **Gridfinity bins don't fit**: Verify 42mm grid spacing and recess depth matches baseplate thickness
- **OpenGrid boards loose**: Check Lite (4mm) vs Full (6.8mm) thickness settings
- **Curved sections support issues**: Enable supports for overhangs, consider orientation
- **HOK connectors misaligned**: Verify consistent riser width across stacked levels

## Workflow Best Practices

1. **Plan layout**: Sketch desk arrangement before printing
2. **Start simple**: Print one straight riser section to test dimensions
3. **Test top plate**: Print small top plate sample to verify recess fit
4. **Iterate height**: Adjust riser height based on actual monitor/keyboard placement
5. **Add curves last**: Print straight sections first, add curved corners after testing
6. **Stack strategically**: Use HOK connectors for multi-level setups only when needed
7. **Integrate grids**: Add Gridfinity/OpenGrid recesses after basic platform is proven

## Compatibility Notes

- Works standalone or integrated with Gridfinity/OpenGrid
- Underware cable channels route naturally under elevated platforms
- French Cleats serve different purpose (wall mounting vs desk elevation)
- Neogrid drawer organization can work below desk, indirect relationship
- Material thickness matters for top plate recesses (Gridfinity baseplate typically 5mm)

## Version History

- **v1.0** (2025-04-17): Initial release
- **v1.1** (2025-04-18): SVG export for top plates
- **v1.2** (2025-04-25): Curved section pieces with arc customization
- **v1.2.1** (2025-04-28): HOK connectors added to bottom of risers
- **v1.3** (2025-05-19): Top plate customizer for Gridfinity/OpenGrid
- **v1.4** (2025-06-06): Riser customizer (slide sides, chamfer)
- **v1.5** (2025-08-10): Split height option for large risers

______________________________________________________________________

*Last updated: December 2025*
*License: CC-BY-NC-SA (non-commercial)*
*Creator: Hands on Katie (Katie)*
*OpenSCAD implementation: BlackjackDuck (Andy)*
