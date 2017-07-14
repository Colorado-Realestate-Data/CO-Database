default = {
    'site': 'http://assessor.co.grand.co.us',
    'init_url': '/assessor/web/',
    'login_url': '/assessor/web/loginPOST.jsp',
    'submit_search_url': '/assessor/taxweb/results.jsp',
    'report_url': '/assessor/eagleweb/report.jsp',
    'eagle_web_url': '/assessor/eagleweb/',
    'report_template_id': 'tax.account.extract.AccountPublic',
    'pagination_re': '^Showing .+ result(s?)',
    'total_pages_re': '(\d+) page',
    'total_records_re1': 'of (\d+) on',
    'total_records_re2': '(\d+) +result',
    'generating_report_pattern': 'Your report is being generated',
    'public_login_data': {'guest': 'true', 'submit': 'Enter EagleWeb'},
}

conf = {
    'grand': {
        'site': 'http://assessor.co.grand.co.us',
    },
    'broomfield': {
        'site': 'http://egov.broomfield.org',
        'report_template_id': 'tax.account.web.extract.AccountPublic',
    },
    'clear_creek': {
        'site': 'http://assessor.co.clear-creek.co.us',
        'init_url': '/Assessor/web/',
        'login_url': '/Assessor/web/loginPOST.jsp',
        'submit_search_url': '/Assessor/taxweb/results.jsp',
        'report_url': '/Assessor/eagleweb/report.jsp',
        'eagle_web_url': '/Assessor/eagleweb/',
    },
    'delta': {
        'site': 'http://itax.deltacounty.com',
    },
    'eagle': {
        'site': 'http://property.eaglecounty.us',
        'report_template_id': 'tax.account.web.extract.AccountPublic',
    },
    'elbert': {
        'site': 'http://services.elbertcounty-co.gov',
    },
    'fremont': {
        'site': 'https://erecords.fremontco.com',
    },
    'garfield': {
        'site': 'https://act.garfield-county.com',
        'report_template_id': 'tax.account.web.extract.AccountPublic',
    },
    'la_plata': {
        'site': 'https://eagleweb.laplata.co.us',
    },
    'las_animas': {
        'site': 'http://208.123.135.187:8080',
    },
    'lincoln': {
        'site': 'http://assessor.lincolncountyco.us',
    },
    'montezuma': {
        'site': 'http://eagleweb.co.montezuma.co.us',
    },
    'montrose': {
        'site': 'http://eagleweb.co.montrose.co.us',
    },
    'morgan': {
        'site': 'http://www.co.morgan.co.us',
    },
    'ouray': {
        'site': 'http://ouraycountyassessor.org',
    },
    'phillips': {
        'site': 'http://phillipsco.tyler-esubmittal.com',
    },
    'routt': {
        'site': 'http://agner.co.routt.co.us',
        'report_template_id': 'tax.account.web.extract.AccountPublic',
    },
}
