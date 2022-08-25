from jinja2 import Environment, PackageLoader, select_autoescape
from lxml import etree

def make_xml(data):
    """
    Function that inserts values into an xml template
    given data from the application.

    Arguments:
    --------------
    data: dictionary
        Dictionary containing information to be
        inserted into the xml template
    Returns:
    -------------
    xml_response: xml
        xml file with templated values
    """
    env = Environment(
        loader=PackageLoader('main', 'templates'),
        autoescape=select_autoescape(['xml'])
    )
    template = "response.template"
    template = env.get_template(template)
    xml = template.render(data=data)
    return(xml)