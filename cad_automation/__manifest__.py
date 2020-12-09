{
    "name": "Cad Automation",
    "summary": "P&ID parsing service",
    # pylint: disable=manifest-deprecated-key
    "description": (
        "Module which provides all required tools and services for parsing "
        "of Piping and Instrumental Diagrams, such as symbol making and registering "
        "into database as well as services which using algorithms parse P&ID diagrams "
        "everything from symbols to lines to text"
    ),
    "author": "QZHub",
    "website": "www.qzhub.com",
    "category": "Parsing",
    "version": "13.0.1.0.0",
    # any module necessary for this one to work correctly
    "depends": ["base", "web"],
    "external_dependencies": {"python": ["cv2", "numpy"], "bin": []},
    # always loaded
    "data": ["security/ir.model.access.csv", "views/views.xml", "views/templates.xml"],
    "qweb": ["static/src/xml/base.xml",],
    # only loaded in demonstration mode
    "application": True,
    "installable": True,
}
