from textx import metamodel_from_file
from textx.export import metamodel_export, PlantUmlRenderer
import os

mm = metamodel_from_file("./grammar/webpage.tx")

pu_file = "mm.pu"
metamodel_export(mm, pu_file, renderer=PlantUmlRenderer())

os.system(f"plantuml -Tsvg {pu_file}")

os.remove(pu_file)

svg_file = "mm.svg"
png_file = "metamodel_plant.png"

os.system(f"convert -background white -flatten {svg_file} {png_file}")

os.remove(svg_file)

print(f"Metamodel exported to {png_file}")
