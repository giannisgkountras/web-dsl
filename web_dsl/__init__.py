"""
Top level package directory of web-dsl
"""

__author__ = """Ioannis Gkountras"""
__email__ = "gkountrasioannis@gmail.com"
__version__ = "0.1.0"

from .language import web_dsl_language, get_metamodel
from .generate import generate
from .m2m.openapi_to_webdsl import transform_openapi_to_webdsl
