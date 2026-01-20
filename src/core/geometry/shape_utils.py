"""
Shape Utilities
Common utility functions for working with CadQuery shapes and OCP geometry.
"""

import cadquery as cq
from typing import List, Optional

# OCP imports for compound handling
from OCP.TopoDS import TopoDS_Compound, TopoDS_Iterator, TopoDS_Solid
from OCP.TopAbs import TopAbs_SOLID, TopAbs_COMPOUND
from OCP.BRep import BRep_Builder


def extract_solids_recursive(shape, solids_list: list) -> None:
    """
    Recursively extract all solids from a shape (including nested compounds).

    This function traverses OCP/TopoDS shapes and extracts all solid geometries,
    handling nested compound structures that can result from multi-segment text
    or complex boolean operations.

    Args:
        shape: OCP TopoDS shape or CadQuery Shape/Workplane to extract solids from.
               Can be a compound, solid, or any TopoDS shape type.
        solids_list: List to append found TopoDS_Solid objects to.
                    Modified in place.

    Example:
        >>> all_solids = []
        >>> extract_solids_recursive(workplane.val(), all_solids)
        >>> print(f"Found {len(all_solids)} solids")
    """
    # Handle CadQuery Shape wrapper
    if hasattr(shape, 'wrapped'):
        shape = shape.wrapped

    shape_type = shape.ShapeType()

    if shape_type == TopAbs_COMPOUND:
        # Iterate through compound children
        iterator = TopoDS_Iterator(shape)
        while iterator.More():
            extract_solids_recursive(iterator.Value(), solids_list)
            iterator.Next()
    elif shape_type == TopAbs_SOLID:
        solids_list.append(shape)


def create_compound(shapes: List) -> cq.Workplane:
    """
    Create a CadQuery Workplane containing a compound of the given shapes.

    This is useful for combining multiple geometries without performing
    boolean operations, which can be faster and avoids potential union failures.

    Args:
        shapes: List of shapes to combine. Can be:
               - OCP TopoDS shapes
               - CadQuery Shape objects
               - CadQuery Workplane objects (extracts .val())

    Returns:
        CadQuery Workplane containing the compound, or empty Workplane if no shapes.

    Example:
        >>> compound = create_compound([shape1, shape2, shape3])
        >>> result = base.union(compound)
    """
    if not shapes:
        return cq.Workplane("XY")

    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)

    for shape in shapes:
        # Handle different input types
        if hasattr(shape, 'val'):
            # CadQuery Workplane
            shape = shape.val()
        if hasattr(shape, 'wrapped'):
            # CadQuery Shape
            shape = shape.wrapped

        builder.Add(compound, shape)

    return cq.Workplane("XY").newObject([cq.Shape(compound)])


def combine_workplanes(workplanes: List[cq.Workplane]) -> Optional[cq.Workplane]:
    """
    Combine multiple CadQuery Workplanes into a single compound Workplane.

    This extracts all shapes from the workplanes and combines them into
    a compound without performing boolean union operations. This is more
    reliable for geometries that might fail standard union operations.

    Args:
        workplanes: List of CadQuery Workplanes to combine.

    Returns:
        Combined Workplane, or None if no valid shapes found.
        Returns the single workplane directly if only one provided.

    Example:
        >>> lines = [generate_line(l) for l in text_lines]
        >>> combined = combine_workplanes(lines)
    """
    if not workplanes:
        return None

    if len(workplanes) == 1:
        return workplanes[0]

    all_shapes = []
    for wp in workplanes:
        if wp is None:
            continue
        try:
            val = wp.val()
            shape = val.wrapped if hasattr(val, 'wrapped') else val
            all_shapes.append(shape)
        except Exception:
            # Try getting solids if val() fails
            try:
                solids = wp.solids().vals()
                for solid in solids:
                    shape = solid.wrapped if hasattr(solid, 'wrapped') else solid
                    all_shapes.append(shape)
            except Exception:
                pass

    if not all_shapes:
        return workplanes[0] if workplanes else None

    return create_compound(all_shapes)


def extract_and_wrap_solids(workplane: cq.Workplane) -> List[cq.Workplane]:
    """
    Extract all solids from a workplane and wrap each as its own Workplane.

    Useful when you need to apply operations to individual solids within
    a compound structure.

    Args:
        workplane: CadQuery Workplane potentially containing multiple solids.

    Returns:
        List of Workplanes, each containing a single solid.

    Example:
        >>> individual_solids = extract_and_wrap_solids(text_geometry)
        >>> for solid in individual_solids:
        ...     result = result.union(solid)
    """
    all_solids = []
    try:
        extract_solids_recursive(workplane.val(), all_solids)
    except Exception:
        return [workplane]

    if not all_solids:
        return [workplane]

    wrapped = []
    for solid in all_solids:
        wrapped.append(cq.Workplane("XY").newObject([cq.Shape(solid)]))

    return wrapped


def union_solids_from_compound(base: cq.Workplane, compound_workplane: cq.Workplane) -> cq.Workplane:
    """
    Union all solids from a compound workplane into a base workplane.

    This handles compound geometries (from multi-segment text, etc.) by
    extracting individual solids and unioning them one at a time, which
    is more reliable than attempting to union the entire compound.

    Args:
        base: Base workplane to union into.
        compound_workplane: Workplane containing compound geometry.

    Returns:
        Base workplane with all solids unioned.

    Example:
        >>> result = union_solids_from_compound(plate_base, text_geometry)
    """
    all_solids = []
    try:
        extract_solids_recursive(compound_workplane.val(), all_solids)
    except Exception:
        # Fallback to regular union
        return base.union(compound_workplane)

    if all_solids:
        for solid in all_solids:
            solid_wp = cq.Workplane("XY").newObject([cq.Shape(solid)])
            base = base.union(solid_wp)
    else:
        # No solids extracted, try regular union
        base = base.union(compound_workplane)

    return base


def cut_solids_from_compound(base: cq.Workplane, compound_workplane: cq.Workplane) -> cq.Workplane:
    """
    Cut all solids from a compound workplane from a base workplane.

    Similar to union_solids_from_compound but performs cut operations.
    Handles compound geometries by extracting individual solids.

    Args:
        base: Base workplane to cut from.
        compound_workplane: Workplane containing compound geometry to cut.

    Returns:
        Base workplane with all solids cut out.

    Example:
        >>> result = cut_solids_from_compound(plate, engraved_text)
    """
    all_solids = []
    try:
        extract_solids_recursive(compound_workplane.val(), all_solids)
    except Exception:
        # Fallback to regular cut
        return base.cut(compound_workplane)

    if all_solids:
        for solid in all_solids:
            solid_wp = cq.Workplane("XY").newObject([cq.Shape(solid)])
            base = base.cut(solid_wp)
    else:
        # No solids extracted, try regular cut
        base = base.cut(compound_workplane)

    return base
