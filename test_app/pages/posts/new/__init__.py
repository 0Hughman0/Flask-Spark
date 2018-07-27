from spark import SubDomain

folder = SubDomain(__file__)
two = folder.Page('err.html')

__subdomain__ = folder