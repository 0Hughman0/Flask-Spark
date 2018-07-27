from spark import SubDomain

folder = SubDomain(__file__)
two = folder.Page('about.html', 'two')

__subdomain__ = folder