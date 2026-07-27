# Neogrid Reference

## What is Neogrid?

Neogrid is an open-source drawer organization system for larger items, designed by Hands on Katie. Unlike Gridfinity (which handles small items), Neogrid uses 3D-printed connectors to join affordable divider materials (MDF, plywood, acrylic, foam board) into custom drawer layouts. It's Gridfinity-compatible and part of the comprehensive home organization framework.

## Core Concept

**Not a fully 3D-printed system** - Neogrid uses:

- **3D-printed connectors** (junctions to join dividers)
- **Store-bought divider material** (MDF, plywood, acrylic, uPVC, foam board, etc.)

This hybrid approach is practical and economical for organizing larger drawer spaces.

## Core Specifications

### Connector System

- **Default material thickness**: 8.5mm (UK standard utility board)
- **Customizable**: Adjust for any material thickness (3mm-9mm+ common)
- **Tolerance**: Material should be ~0.15mm smaller than connector spacing for snug fit
- **Connector types**: X-junction, T-junction, L-junction, I-junction (top and bottom pieces)

### Divider Lengths

- **Recommended**: 160mm (flexible, universal for home use)
- **Gridfinity compatible**: Use multiples of 42mm for alignment (e.g., 42mm x 4 - 8.5mm = 159.5mm â‰ˆ 160mm)
- **Custom lengths**: Any length works, but consistent lengths throughout the home maximize flexibility

### Junction Pieces

- **X-junction**: Most versatile, use at intersections (most common)
- **T-junction**: Edge connections and three-way joins
- **L-junction**: Corner connections
- **I-junction**: Straight top pieces, also used standalone when not using Gridfinity base

## Gridfinity Compatibility

### Integration Options

- **With Gridfinity base**: Align Neogrid connectors on Gridfinity baseplate for positioning
- **Without Gridfinity**: Use bottom connectors upside-down as standalone feet
- **Mixed systems**: Combine small Gridfinity bins with large Neogrid compartments in same drawer

### Alignment

- Bottom connectors designed to snap onto Gridfinity 42mm grid
- Ensures proper spacing and easy repositioning
- Gridfinity base helps position connectors accurately

## Print Settings

- **Layer height**: 0.2mm
- **Walls**: 3 walls
- **Infill**: 10-15%
- **Material**: PLA or PETG
- **Test print**: Always print one X-junction to verify material fit before batch printing

## Material Options

### Common Divider Materials

- **MDF**: 3mm, 6mm, 8mm, 9mm (affordable, paintable)
- **Plywood**: 6mm, 8mm (strong, natural look)
- **uPVC utility/soffit board**: 8.5mm UK standard (minimal painting, long lengths)
- **Acrylic**: Various thicknesses (transparent, modern aesthetic)
- **Foam poster board**: ~5mm / 3/16" (lightweight, US-friendly)
- **1/4" material**: 6.35mm (common US size)

### Material Selection Tips

- Measure actual thickness after painting
- Longer lengths reduce cutting but less flexible
- Consider drawer depth when choosing material height
- Lighter materials better for furniture drawer weight limits

## Versions

### Neogrid 1.0 (Original)

- Fusion 360 parametric file
- Adjust material thickness parameter
- Manual export of STL files
- Fixed connector designs

### Neogrid 2.0 (Current)

- Fully parametric OpenSCAD customizer
- Web-based generator
- OpenGrid compatibility added
- Material grip features optional
- Screw mounting options
- More customization options

## Design Principles

- Affordable: Use cheap store-bought materials
- Adaptable: Easy to reconfigure as needs change
- Compatible: Works with or without Gridfinity
- Practical: Right-sized for larger items (clothes, tools, kitchen items)
- Standards-based: Aligns to modular grid systems

## Official Resources

**Main Documentation:**

- Guide: <https://handsonkatie.com/neogrid-organise-your-big-items-with-this-free-and-open-source-system/>
- Home organization framework: <https://handsonkatie.com/the-ultimate-home-organisation-system/>

**Downloads:**

- Neogrid 1.0 (Printables): <https://www.printables.com/model/844086-neogrid-the-complete-home-organisational-system-fo>
- Neogrid 1.0 (MakerWorld): <https://makerworld.com/en/models/545102-neogrid-the-complete-home-organisational-system>
- Neogrid 2.0 (MakerWorld): <https://makerworld.com/en/models/1501061-neogrid-2-0-drawer-management-system>

**Video:**

- Introduction video on Hands on Katie YouTube channel

**Community:**

- Hands on Katie Discord server
- Hands on Katie Patreon community

## Common Use Cases

- Clothing drawers (dressing room organization)
- Kitchen utensil drawers
- Workshop tool drawers
- Craft room supply drawers
- Cable and accessory storage
- Any drawer with items too large for Gridfinity

## Setup Quick Reference

1. **Choose material**: Select divider material from local hardware/craft store
2. **Measure thickness**: After painting if applicable
3. **Print test**: One X-junction with adjusted thickness parameter
4. **Verify fit**: Material should friction-fit securely
5. **Cut dividers**: To desired lengths (160mm recommended)
6. **Print connectors**: Start with X-junctions (most versatile)
7. **Assemble**: Snap bottom and top connectors onto dividers
8. **Install**: Place in drawer (optionally on Gridfinity base)
9. **Iterate**: Add T, L, I pieces as needed for custom layouts

## Troubleshooting

- **Connectors too loose**: Decrease material thickness parameter by 0.1-0.2mm
- **Connectors too tight**: Increase material thickness parameter by 0.1-0.2mm
- **Material warping**: Use stiffer material or add more support connectors
- **Without Gridfinity**: Use bottom pieces upside-down as feet
- **Material sourcing**: Check hardware stores (Obi, Hornbach, Bauhaus in EU; Home Depot, Lowe's in US)

## Customization

### Fusion 360 (v1.0)

- Open .f3d file in Fusion 360 (free personal version)
- Modify "NeoGridWidth" parameter
- Export desired pieces as STL

### OpenSCAD Customizer (v2.0)

- Web-based generator (no software install)
- Adjust material thickness
- Toggle material grip features
- Set Gridfinity or OpenGrid compatibility
- Export custom STL files

## Compatibility Notes

- Works standalone or with Gridfinity base
- Neogrid 2.0 adds OpenGrid support
- Can mix with Underware for cable management
- Part of integrated home organization ecosystem

______________________________________________________________________

*Last updated: October 2025*
*License: Check individual files (typically open source)*
*Creator: Hands on Katie (Katie)*
