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
    'records_per_page': 100,
    'generating_report_pattern': 'Your report is being generated',
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
        'records_per_page': 10,
    },
}
