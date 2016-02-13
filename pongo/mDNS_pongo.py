from zeroconf import ServiceBrowser, Zeroconf

class MyListener(object):

    def remove_service(self, zeroconf, service_type, name):
        print("Service %s removed" % (name,))

    def add_service(self, zeroconf, service_type, name):
        info = zeroconf.get_service_info(service_type, name)
        print "Service %s added" % info.name
        print '.'.join([str(ord(c)) for c in info.address]) + ':%s'%info.port

zeroconf = Zeroconf()
listener = MyListener()
browser = ServiceBrowser(zeroconf, "_http._tcp.local.", listener)
