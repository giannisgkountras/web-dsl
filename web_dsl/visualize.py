import os
from textx import metamodel_from_file
from textx.export import metamodel_export

entity_mm = metamodel_from_file("./web-dsl/grammar/syntax/screens.tx")

metamodel_export(entity_mm, "entity.dot")

# Run the following command to generate the image:
os.system("dot -Tpng entity.dot -o metamodel.png")

# Remove the .dot file
os.remove("entity.dot")

# Show the image
print("Entity metamodel exported to metamodel.png")
