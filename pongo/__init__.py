class PongoServer:
    def __init__(self, name, ip_address):
        self.name = name
        self.ip_address = ip_address
        
    def __eq__(self, other):
        return self.ip_address == other.ip_address

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return '%s (%s)'%(self.name, self.ip_address)
