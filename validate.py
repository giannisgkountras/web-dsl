from textx import metamodel_from_file

base_path = "./web-dsl/grammar/syntax/"


def validate_grammar(grammar_file):
    try:
        metamodel = metamodel_from_file(grammar_file)
        print(f"✅ The grammar '{grammar_file}' is valid!")
    except Exception as e:
        print(f"❌ Error in grammar: {e}")


# Usage:
validate_grammar(base_path + "screens.tx")
