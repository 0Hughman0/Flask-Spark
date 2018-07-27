from spark import SubDomain

folder = SubDomain(__file__)
home = folder.Page('home.html')
about = folder.Page('about.html')

__subdomain__ = folder
