from textx import get_children_of_type, TextXSemanticError


def validate_model(model, main_file):
    """Validates the model."""

    validate_webpage(model, main_file)

    all_entities = get_children_of_type("Entity", model)
    strict_entities = strict_entities = [e for e in all_entities if e.strict]

    all_components = get_children_of_type("Component", model)
    components_referencing_strict_entities = [
        c for c in all_components if c.entity and c.entity in strict_entities
    ]

    # Validate components with strict entities
    errors = validate_components_with_strict_entities(
        components_referencing_strict_entities
    )

    # # Validate repetitions with strict entities
    # all_repetitions = get_children_of_type("Repetition", model)
    # repetitions_to_check = [
    #     r for r in all_repetitions if r.entity and r.entity in strict_entities
    # ]
    # for repetition in repetitions_to_check:
    #     attribute_root = repetition.item[0]
    #     strict_entity_attributes = repetition.entity.attributes
    #     strict_entity_attributes_names = [a.name for a in strict_entity_attributes]
    #     if attribute_root not in strict_entity_attributes_names:
    #         errors.append(
    #             f"Repetition uses attribute '{attribute_root}' not allowed by strict entity '{repetition.entity.name}'"
    #         )

    # Validate conditions with strict entities
    # all_conditions = get_children_of_type("Condition", model)
    # conditions_to_check = [
    #     c for c in all_conditions if c.entity and c.entity in strict_entities
    # ]
    # for item in conditions_to_check:
    #     strict_entity_attributes = item.entity.attributes
    #     strict_entity_attributes_names = [a.name for a in strict_entity_attributes]
    #     condition = item.condition
    #     flat_primitives = find_flat_primitive_lists(condition)

    #     for primitive in flat_primitives:
    #         attribute_root = primitive[0]

    #         if attribute_root not in strict_entity_attributes_names:
    #             errors.append(
    #                 f"Condition uses attribute '{attribute_root}' not allowed by strict entity '{item.entity.name}'"
    #             )

    # Validate CRUD table
    all_crud_tables = get_children_of_type("CrudTable", model)
    validate_crud_table(all_crud_tables, errors)

    if errors:
        error_text = "\n".join(f" - {e}" for e in errors)
        raise TextXSemanticError(
            f"Model validation failed with {len(errors)} errors:\n{error_text}"
        )


def validate_webpage(model, main_file):
    """
    Validate that only the main file contains a webpage definition.
    """
    # Check if the main file has exactly one webpage
    if not model.webpage:
        raise Exception(
            f"Main file {main_file} must contain exactly one 'webpage' definition."
        )

    # Check imported files (recursively loaded models are accessible via _tx_model_repository)
    for imported_model in model._tx_model_repository.all_models:
        if imported_model != model and imported_model.webpage:
            raise Exception(
                f"Imported file {imported_model._tx_filename} contains a 'webpage' definition, which is only allowed in the main file."
            )


def validate_components_with_strict_entities(components):
    errors = []
    for component in components:
        if not hasattr(component, "entity") or not component.entity:
            continue

        if not getattr(component.entity, "strict", False):
            continue

        # Collect all formatted attribute paths from the component type
        attribute_paths = []

        # Find all attributes that look like formatted paths (lists of mixed str/int)
        for attr_name in dir(component.type):
            if attr_name.startswith("_"):
                continue
            attr = getattr(component.type, attr_name)
            if isinstance(attr, list) and all(isinstance(p, (int, str)) for p in attr):
                attribute_paths.append(attr)
            elif isinstance(attr, list) and all(
                isinstance(p, list) and all(isinstance(e, (int, str)) for e in p)
                for p in attr
            ):
                # This handles lists of paths, like yValues = [[0, 'temp'], [0, 'pressure']]
                attribute_paths.extend(attr)

        strict_entity_attributes = component.entity.attributes
        strict_entity_attributes_names = [a.name for a in strict_entity_attributes]

        for attribute in attribute_paths:
            if not attribute:  # skip empty lists
                continue
            attribute_root = attribute[0]

            if attribute_root not in strict_entity_attributes_names:
                errors.append(
                    f"Component '{component.name}' uses attribute '{attribute_root}' not allowed by strict entity '{component.entity.name}'"
                )
                continue
    return errors


def validate_crud_table(all_crud_tables, errors):
    """Validates the CRUD table. If it has a reference to a MySQLQuery, it needs to have a table name."""
    for crud_table in all_crud_tables:
        entity_referenced_by_crud_table = crud_table.parent.entity
        source_of_entity = entity_referenced_by_crud_table.source

        if source_of_entity.__class__.__name__ == "MySQLQuery":
            if crud_table.table is None or crud_table.table == "":
                errors.append(
                    f"CRUD table '{crud_table.name}' references a MySQLQuery without a table name."
                )
            else:
                continue


def find_flat_primitive_lists(expr):
    result = []

    def recurse(sub):
        if isinstance(sub, list):
            # Check that all elements are str or int, and none are lists
            if all(isinstance(x, (str, int)) for x in sub):
                result.append(sub)
            else:
                for item in sub:
                    recurse(item)

    recurse(expr)
    return result
