# -*- coding: utf-8 -*-

# noinspection PyStatementEffect
{
    'name': 'SilkSoft Dashboards',
    'version': '15.0.1.0001',
    'category': 'Productivity',
    'sequence': 40,
    'summary': 'Module to display dashboards for managers and employees ',
    'description': """Module to display dashboards for managers and employees""",
    'website': 'https://silksoft.org',
    'author': 'SilkSoft Inc',
    'license': 'AGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/dashboard_view.xml',
        'views/dynamic_block_view.xml',
        'views/dashboard_menu_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'silksoft_dashboards/static/src/js/dynamic_dashboard.js',
            'silksoft_dashboards/static/src/scss/style.scss',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.8.0/Chart.bundle.js',
            'https://fonts.googleapis.com/css?family=Source+Sans+Pro:300,400,400i,700',
        ],
        'web.assets_qweb': [
            'silksoft_dashboards/static/src/xml/dynamic_dashboard_template.xml',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
