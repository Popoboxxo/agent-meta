# Common Enhancements

Add these to any pattern:

## Label Recess

Add a recessed area on the front for labels.

```openscad
module add_label_recess() {
    difference() {
        basic_bin();  // Your pattern
        
        // Label cutout on front
        translate([
            internal_width/2 - 20,
            internal_depth + wall_thickness - 0.5,
            internal_height - 15
        ])
            label_recess(width=40, height=10);
    }
}

module label_recess(width, height, depth=1) {
    // 45° angle - no supports needed
    hull() {
        translate([0, 0, 0])
            cube([width, depth, 0.1]);
        translate([0, depth, height])
            cube([width, 0.1, 0.1]);
    }
}
```

## Drainage Holes

Add drainage holes to the bottom of bins to allow water to escape.

```openscad
module add_drainage() {
    difference() {
        basic_bin();
        
        // Grid of holes in bottom
        for (x = [10:15:internal_width-10]) {
            for (y = [10:15:internal_depth-10]) {
                translate([x, y, -base_thickness-1])
                    cylinder(h=base_thickness+2, d=5, $fn=20);
            }
        }
    }
}
```

## Rounded Corners

Add rounded corners to the design for a softer look and easier cleaning.

```openscad
module rounded_basket(corner_r=3) {
    hull() {
        for (x = [corner_r, internal_width - corner_r]) {
            for (y = [corner_r, internal_depth - corner_r]) {
                for (z = [0, internal_height - corner_r]) {
                    translate([x, y, z])
                        sphere(r=corner_r, $fn=20);
                }
            }
        }
    }
}
```

## Finger Scoop

Add a finger scoop cutout on the front wall for easier access to contents.

```openscad
module add_finger_scoop() {
    difference() {
        basic_bin();
        
        // Scoop cutout in front
        translate([
            internal_width/2,
            internal_depth + wall_thickness,
            internal_height - 15
        ])
            rotate([90, 0, 0])
                cylinder(h=wall_thickness+2, d=30, $fn=40);
    }
}
```
